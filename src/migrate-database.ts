import { Client, isFullPage, APIResponseError } from "@notionhq/client";
import {
  PageObjectResponse,
  BlockObjectRequest,
  DatabaseObjectResponse,
} from "@notionhq/client/build/src/api-endpoints";
import dotenv from "dotenv";
import { NotionHugoDatabaseSetup } from "./utils/setup";

dotenv.config();

// 검증 및 변환 인터페이스
interface ValidationOptions {
  validSelectOptions: { [key: string]: string[] };
  defaultOptions: { [key: string]: string };
}

interface BlockValidationResult {
  isValid: boolean;
  errors: string[];
  block: BlockObjectRequest | null;
}

interface MigrationResult {
  success: boolean;
  pageId: string;
  errors: string[];
  retryCount: number;
}

interface MigrationStats {
  total: number;
  success: number;
  failed: number;
  skipped: number;
  errors: { [pageId: string]: string[] };
}

// 유틸리티 함수
function validateSelectOption(
  value: string,
  field: string,
  options: ValidationOptions,
): string {
  const validOptions = options.validSelectOptions[field] || [];
  const defaultOption = options.defaultOptions[field] || "Uncategorized";
  return validOptions.includes(value) ? value : defaultOption;
}

async function retryWithFallback<T>(
  operation: () => Promise<T>,
  fallback: () => void,
  maxRetries: number = 3,
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (
        error instanceof APIResponseError &&
        error.message?.includes("invalid select option")
      ) {
        fallback();
      } else {
        throw error;
      }
    }
  }

  throw lastError || new Error("Max retries exceeded");
}

function logMigrationProgress(stats: MigrationStats): void {
  console.info(`
Migration Progress:
- Total: ${stats.total}
- Success: ${stats.success}
- Failed: ${stats.failed}
- Skipped: ${stats.skipped}
  `);

  if (stats.failed > 0) {
    console.error("\nFailed pages:");
    Object.entries(stats.errors).forEach(([pageId, errors]) => {
      console.error(`\nPage ${pageId}:`);
      errors.forEach((error) => console.error(`- ${error}`));
    });
  }
}

// 설정 및 매핑
const REQUIRED_FIELDS: { [key: string]: string[] } = {
  image: ["external.url"],
  file: ["external.url"],
  pdf: ["external.url"],
  video: ["external.url"],
  table: ["table_width", "has_column_header", "has_row_header", "children"],
  column_list: ["children"],
  column: ["children"],
  bookmark: ["url"],
  embed: ["url"],
};

const DEFAULT_OPTIONS: ValidationOptions = {
  validSelectOptions: {
    Tags: [], // 대상 데이터베이스에서 동적으로 채워질 예정
  },
  defaultOptions: {
    Tags: "Uncategorized",
  },
};

const TAG_MAPPINGS: { [key: string]: string } = {
  // 여기에 필요한 태그 매핑을 추가
  // 예: 'old_tag': 'new_tag'
};

// 블록 유효성 검사
function validateBlock(block: BlockObjectRequest): boolean {
  const type = block.type;
  const requiredFields = REQUIRED_FIELDS[type as keyof typeof REQUIRED_FIELDS];

  if (!requiredFields) return true; // 필수 필드가 정의되지 않은 타입은 통과

  return requiredFields.every((field: string) => {
    const fieldPath = field.split(".");
    let value: unknown = block[type as keyof BlockObjectRequest];

    for (const key of fieldPath) {
      if (!value || typeof value !== "object") return false;
      value = (value as Record<string, unknown>)[key];
    }

    return value !== undefined && value !== null;
  });
}

// 블록 변환
function transformBlock(block: BlockObjectRequest): BlockObjectRequest | null {
  const type = block.type;

  switch (type) {
    case "image":
    case "file":
    case "pdf":
    case "video":
      if (!validateBlock(block)) {
        console.warn(`Skipping invalid ${type} block: missing external URL`);
        return null;
      }
      break;

    case "table":
      if (!validateBlock(block)) {
        const tableBlock = block as any;
        tableBlock.table.table_width = tableBlock.table.table_width || 1;
        tableBlock.table.has_column_header =
          tableBlock.table.has_column_header || false;
        tableBlock.table.has_row_header =
          tableBlock.table.has_row_header || false;
        tableBlock.table.children = tableBlock.table.children || [];
      }
      break;

    case "column_list":
    case "column":
      if (!validateBlock(block)) {
        const columnBlock = block as any;
        columnBlock[type].children = columnBlock[type].children || [];
      }
      break;
  }

  return block;
}

// 코드 블록 분할
function splitCodeBlock(block: BlockObjectRequest): BlockObjectRequest[] {
  const codeBlock = block as any;
  if (
    codeBlock.type !== "code" ||
    !codeBlock.code?.rich_text?.[0]?.text?.content
  ) {
    return [block];
  }

  const content = codeBlock.code.rich_text[0].text.content;
  const MAX_LENGTH = 2000;

  if (content.length <= MAX_LENGTH) {
    return [block];
  }

  const blocks: BlockObjectRequest[] = [];
  let remainingContent = content;

  while (remainingContent.length > 0) {
    const chunk = remainingContent.slice(0, MAX_LENGTH);
    remainingContent = remainingContent.slice(MAX_LENGTH);

    const newBlock = {
      object: "block",
      type: "code",
      code: {
        ...codeBlock.code,
        rich_text: [
          {
            type: "text",
            text: { content: chunk },
            annotations: codeBlock.code.rich_text[0].annotations || {},
          },
        ],
      },
    };

    blocks.push(newBlock as BlockObjectRequest);
  }

  return blocks;
}

// 프로퍼티 변환
function transformProperties(properties: any): any {
  const transformed = { ...properties };

  // Tags 변환
  if (
    transformed.Tags?.type === "multi_select" &&
    transformed.Tags.multi_select
  ) {
    transformed.Tags.multi_select = transformed.Tags.multi_select.map(
      (tag: any) => ({
        ...tag,
        name: TAG_MAPPINGS[tag.name] || tag.name,
      }),
    );
  }

  return transformed;
}

interface MigrationConfig {
  sourceDbId: string;
  parentPageId: string;
  targetFolder: string;
}

interface PropertyValidationResult {
  missingRequired: string[];
  incompatibleTypes: Array<{
    property: string;
    expectedType: string;
    actualType: string;
  }>;
}

async function validateSourceDatabase(
  notion: Client,
  sourceDbId: string,
): Promise<PropertyValidationResult> {
  const result: PropertyValidationResult = {
    missingRequired: [],
    incompatibleTypes: [],
  };

  // Get database schema
  const database = await notion.databases.retrieve({
    database_id: sourceDbId,
  });

  // Required properties and their expected types
  const requiredProperties = {
    Name: "title",
    isPublished: "checkbox",
    Description: "rich_text",
    Tags: "multi_select",
    "Created time": "date",
    "Last Updated": "last_edited_time",
  };

  // Check for missing required properties
  for (const [propName, expectedType] of Object.entries(requiredProperties)) {
    const prop = database.properties[propName];
    if (!prop) {
      result.missingRequired.push(propName);
    } else if (prop.type !== expectedType) {
      // Special handling for time-related properties
      if (
        (propName === "Created time" &&
          (prop.type === "date" || prop.type === "created_time")) ||
        (propName === "Last Updated" &&
          (prop.type === "last_edited_time" || prop.type === "date"))
      ) {
        // These types are acceptable, don't report as incompatible
        continue;
      }

      result.incompatibleTypes.push({
        property: propName,
        expectedType,
        actualType: prop.type,
      });
    }
  }

  return result;
}

async function migratePages(
  notion: Client,
  sourceDbId: string,
  targetDbId: string,
) {
  const stats: MigrationStats = {
    total: 0,
    success: 0,
    failed: 0,
    skipped: 0,
    errors: {},
  };

  try {
    // Get valid select options from target database
    const targetDb = await notion.databases.retrieve({
      database_id: targetDbId,
    });

    if (targetDb.properties.Tags?.type === "multi_select") {
      DEFAULT_OPTIONS.validSelectOptions.Tags =
        targetDb.properties.Tags.multi_select.options.map(
          (option) => option.name,
        );
    }

    // Validate database structure
    console.info("Validating source database structure...");
    const validationResult = await validateSourceDatabase(notion, sourceDbId);

    if (
      validationResult.missingRequired.length > 0 ||
      validationResult.incompatibleTypes.length > 0
    ) {
      console.error("\nDatabase validation failed:");

      if (validationResult.missingRequired.length > 0) {
        console.error("\nMissing required properties:");
        validationResult.missingRequired.forEach((prop) => {
          console.error(`- ${prop}`);
        });
      }

      if (validationResult.incompatibleTypes.length > 0) {
        console.error("\nIncompatible property types:");
        validationResult.incompatibleTypes.forEach(
          ({ property, expectedType, actualType }) => {
            console.error(
              `- ${property}: expected ${expectedType}, found ${actualType}`,
            );
          },
        );
      }

      throw new Error(
        "Database validation failed. Please fix the issues and try again.",
      );
    }

    console.info("Database validation successful!");

    // Get all pages from source database
    const pages = await notion.databases.query({
      database_id: sourceDbId,
    });

    stats.total = pages.results.length;
    console.info(`Found ${stats.total} pages to migrate`);

    for (const pageResult of pages.results) {
      if (!isFullPage(pageResult)) {
        console.warn(`Skipping page ${pageResult.id}: Not a full page object`);
        stats.skipped++;
        continue;
      }

      const page = pageResult as PageObjectResponse;
      try {
        // Extract content and properties
        const blocks = await notion.blocks.children.list({
          block_id: page.id,
        });

        // Transform blocks with validation and splitting
        const transformedBlocks: BlockObjectRequest[] = [];
        for (const block of blocks.results as BlockObjectRequest[]) {
          if (!validateBlock(block)) {
            console.warn(`Skipping invalid block of type: ${block.type}`);
            continue;
          }

          const transformedBlock = transformBlock(block);
          if (transformedBlock) {
            if (
              (block as any).type === "code" &&
              (block as any).code?.rich_text?.[0]?.text?.content &&
              (block as any).code.rich_text[0].text.content.length > 2000
            ) {
              const splitBlocks = splitCodeBlock(block);
              transformedBlocks.push(...splitBlocks);
            } else {
              transformedBlocks.push(transformedBlock);
            }
          }
        }

        // Transform properties with retry logic
        const properties = transformProperties({
          Name: {
            title:
              page.properties.Name?.type === "title"
                ? page.properties.Name.title
                : [],
          },
          isPublished: {
            type: "checkbox",
            checkbox:
              page.properties.isPublished?.type === "checkbox"
                ? page.properties.isPublished.checkbox
                : false,
          },
          Description: {
            type: "rich_text",
            rich_text:
              page.properties.Description?.type === "rich_text"
                ? page.properties.Description.rich_text
                : [],
          },
          Tags: {
            type: "multi_select",
            multi_select:
              page.properties.Tags?.type === "multi_select"
                ? page.properties.Tags.multi_select.map((tag) => ({
                    ...tag,
                    name: validateSelectOption(
                      tag.name,
                      "Tags",
                      DEFAULT_OPTIONS,
                    ),
                  }))
                : [],
          },
          "Created time":
            page.properties["Created time"]?.type === "date"
              ? {
                  type: "date",
                  date: page.properties["Created time"].date,
                }
              : {
                  type: "date",
                  date: {
                    start: page.created_time,
                  },
                },
          Author: {
            type: "rich_text",
            rich_text:
              page.properties.Author?.type === "rich_text"
                ? (page.properties.Author.rich_text as any)
                : ([
                    {
                      type: "text",
                      text: { content: "Gunn Kim" },
                    },
                  ] as any),
          },
          ShowToc: {
            type: "checkbox",
            checkbox:
              page.properties.ShowToc?.type === "checkbox"
                ? page.properties.ShowToc.checkbox
                : true,
          },
          HideSummary: {
            type: "checkbox",
            checkbox:
              page.properties.HideSummary?.type === "checkbox"
                ? page.properties.HideSummary.checkbox
                : false,
          },
          isFeatured: {
            type: "checkbox",
            checkbox:
              page.properties.isFeatured?.type === "checkbox"
                ? page.properties.isFeatured.checkbox
                : false,
          },
          Subtitle: {
            type: "rich_text",
            rich_text:
              page.properties.Subtitle?.type === "rich_text"
                ? page.properties.Subtitle.rich_text
                : [],
          },
        });

        // Create new page with retry logic
        await retryWithFallback(
          async () =>
            await notion.pages.create({
              parent: {
                database_id: targetDbId,
              },
              properties,
              children: transformedBlocks,
            }),
          () => {
            // Reset tags to default on error
            properties.Tags.multi_select = properties.Tags.multi_select.map(
              (tag: any) => ({
                ...tag,
                name: DEFAULT_OPTIONS.defaultOptions.Tags,
              }),
            );
          },
        );

        console.info(`Migrated page: ${page.id}`);
        stats.success++;
      } catch (error) {
        console.error(`Failed to migrate page ${page.id}:`, error);
        stats.failed++;
        stats.errors[page.id] = [(error as Error).message];
      }
    }

    logMigrationProgress(stats);
    console.info("Migration completed!");
  } catch (error) {
    console.error("Migration failed:", error);
    process.exit(1);
  }
}

async function main() {
  const sourceDbId = process.argv[2];
  const parentPageId = process.argv[3];
  const targetFolder = process.argv[4] || "posts";
  const notionToken = process.env.NOTION_TOKEN;

  if (!sourceDbId || !parentPageId) {
    console.error("Error: Source database ID and parent page ID are required");
    console.error(
      "Usage: npm run migrate-database <source-db-id> <parent-page-id> [target-folder]",
    );
    process.exit(1);
  }

  if (!notionToken) {
    console.error("Error: NOTION_TOKEN environment variable is not set");
    process.exit(1);
  }

  const notion = new Client({ auth: notionToken });

  try {
    // First, create new database with our structure
    console.info("Creating new database...");
    const setup = new NotionHugoDatabaseSetup({
      parentPageId,
      databaseName: "Migrated Hugo Blog Posts",
      notionToken,
    });
    const newDb = await setup.createHugoDatabase();
    console.info("New database created:", newDb.id);

    // Migrate content from old database
    console.info("Starting migration...");
    await migratePages(notion, sourceDbId, newDb.id);

    // Update config file
    const configContent = `import { defineConfig } from "./src/config";

export default defineConfig({
  mount: {
    manual: true,
    databases: [
      {
        database_id: "${newDb.id}",
        target_folder: "${targetFolder}"
      }
    ]
  }
});
`;
    require("fs").writeFileSync("notion-hugo.config.ts", configContent);
    console.info(
      "Updated notion-hugo.config.ts with new database configuration",
    );

    console.info("\nMigration completed!");
    console.info(
      "1. Open the new database in Notion:",
      `https://notion.so/${newDb.id.replace(/-/g, "")}`,
    );
    console.info("2. Configuration has been updated automatically");
    console.info("3. Run 'npm start' to begin syncing your posts");
  } catch (error) {
    console.error("Setup failed:", error);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
