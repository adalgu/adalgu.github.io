import fs from "fs-extra";
import { Client, iteratePaginatedAPI } from "@notionhq/client";
import { PageObjectResponse } from "@notionhq/client/build/src/api-endpoints";
import { NotionToMarkdown } from "./markdown/notion-to-md";
import YAML from "yaml";
import { sh } from "./sh";
import { DatabaseMount, PageMount } from "./config";
import { getPageTitle, getCoverLink, getFileName } from "./helpers";
import { MdBlock } from "./markdown/types";
import path from "path";
import { getContentFile } from "./file";
import {
  NotionToHugoMapping,
  ConversionResult,
  BatchProcessResult,
  DEFAULT_HUGO_SETTINGS,
  MAX_IMAGE_SIZE,
} from "./types";
import { calculateContentHash, hasContentChanged } from "./utils/hash";
import { validatePage, ValidationError } from "./utils/validation";

async function processCoverImage(
  page: PageObjectResponse,
  notion: Client,
): Promise<{ image?: string; alt?: string; caption?: string } | null> {
  try {
    const coverLink = await getCoverLink(page.id, notion);
    if (!coverLink) return null;

    // Basic validation
    if (coverLink.link.length === 0) {
      throw new Error("Empty cover image URL");
    }

    return {
      image: coverLink.link,
      alt: getPageTitle(page),
      caption: "", // Could be extended to get caption from Notion if available
    };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.warn(`[Warn] Cover image processing failed: ${errorMessage}`);
    return null;
  }
}

// Helper functions for property access
function getPropertyText(property: any): string {
  if (property?.type === "rich_text" && Array.isArray(property.rich_text)) {
    return property.rich_text.map((item: any) => item.plain_text).join("");
  }
  return "";
}

function getPropertyTags(property: any): string[] {
  if (
    property?.type === "multi_select" &&
    Array.isArray(property.multi_select)
  ) {
    return property.multi_select.map((tag: any) => tag.name);
  }
  return [];
}

function getExpiryTime(
  blocks: MdBlock[],
  expiry_time: string | undefined = undefined,
): string | undefined {
  for (const block of blocks) {
    if (block.expiry_time !== undefined) {
      if (expiry_time === undefined) expiry_time = block.expiry_time;
      else
        expiry_time =
          expiry_time < block.expiry_time ? expiry_time : block.expiry_time;
    }
    if (block.children.length > 0) {
      const child_expiry_time = getExpiryTime(block.children, expiry_time);
      if (child_expiry_time) {
        if (expiry_time === undefined) expiry_time = child_expiry_time;
        else
          expiry_time =
            expiry_time < child_expiry_time ? expiry_time : child_expiry_time;
      }
    }
  }
  return expiry_time;
}

export async function renderPage(
  page: PageObjectResponse,
  notion: Client,
): Promise<{ title: string; pageString: string; hash: string }> {
  try {
    // Validate page
    const validationErrors = validatePage(page);
    if (validationErrors.length > 0) {
      throw new Error(
        `Validation errors: ${validationErrors
          .map((e) => `${e.property}: ${e.message}`)
          .join(", ")}`,
      );
    }

    // Initialize markdown converter
    const n2m = new NotionToMarkdown({ notionClient: notion });
    n2m.setUnsupportedTransformer((type) => {
      return `{{< notion-unsupported-block type=${type} >}}`;
    });

    // Configure custom transformers for better Hugo compatibility
    n2m.setCustomTransformer("callout", async (block: any) => {
      if (block.type === "callout" && block.callout) {
        const emoji =
          block.callout.icon?.type === "emoji"
            ? block.callout.icon.emoji
            : "💡";
        const text = block.callout.rich_text
          .map((t: { plain_text: string }) => t.plain_text)
          .join("");
        return `> ${emoji} **Note:** ${text}\n\n`;
      }
      return "";
    });

    // Convert content
    const mdblocks = await n2m.pageToMarkdown(page.id);
    const mdString = n2m.toMarkdownString(mdblocks);
    const title = getPageTitle(page);

    // Get published date
    let publishedDate: string;
    if (
      page.properties["Published"] &&
      page.properties["Published"].type === "date" &&
      page.properties["Published"].date &&
      page.properties["Published"].date.start
    ) {
      publishedDate = page.properties["Published"].date.start;
    } else {
      publishedDate = page.last_edited_time;
    }

    // Process cover image
    const cover = await processCoverImage(page, notion);

    // Calculate content hash
    const hash = calculateContentHash(page);

    // Prepare frontmatter
    const frontMatter: NotionToHugoMapping = {
      ...DEFAULT_HUGO_SETTINGS,
      title,
      date: publishedDate,
      lastmod: page.last_edited_time,
      draft:
        page.properties.isPublished?.type === "checkbox"
          ? !page.properties.isPublished.checkbox
          : undefined,
      description: getPropertyText(page.properties.Description) || "",
      tags: getPropertyTags(page.properties.Tags) || [],
      author: getPropertyText(page.properties.Author) || "Gunn Kim",
      cover: cover || undefined,
      featured:
        page.properties.isFeatured?.type === "checkbox"
          ? page.properties.isFeatured.checkbox
          : undefined,
      subtitle: getPropertyText(page.properties.Subtitle) || undefined,
      NOTION_METADATA: {
        id: page.id, // Ensure page ID is saved
        convertedToHugo: true,
        lastConvertedAt: new Date().toISOString(),
        conversionHash: hash,
        needsReview: false,
        hugoPath: "",
      },
    };

    // Handle slug - use Slug property if it exists, otherwise use title
    const slugValue =
      page.properties["Slug"]?.type === "rich_text"
        ? page.properties["Slug"].rich_text
            .map((item) => item.plain_text)
            .join("")
            .trim()
        : "";

    if (slugValue) {
      (frontMatter as any).slug = slugValue;
    } else {
      // If no slug provided, create one from title
      (frontMatter as any).slug = title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
    }

    if (page.properties["Subtitle"]?.type === "rich_text") {
      const subtitleValue = page.properties["Subtitle"].rich_text
        .map((item) => item.plain_text)
        .join("")
        .trim();
      if (subtitleValue) {
        (frontMatter as any).subtitle = subtitleValue;
      }
    }

    // Generate page string
    return {
      title,
      pageString:
        "---\n" +
        YAML.stringify(frontMatter, {
          defaultStringType: "QUOTE_DOUBLE",
          defaultKeyType: "PLAIN",
        }) +
        "\n---\n" +
        mdString,
      hash,
    };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to render page: ${errorMessage}`);
  }
}

export async function savePage(
  page: PageObjectResponse,
  notion: Client,
  mount: DatabaseMount | PageMount,
): Promise<ConversionResult> {
  try {
    const postpath = path.join(
      "content",
      mount.target_folder,
      getFileName(getPageTitle(page), page.id),
    );

    // Check if file exists and has changed
    const post = getContentFile(postpath);
    if (
      post &&
      !hasContentChanged(page, (post.metadata as any).conversionHash)
    ) {
      console.info(`[Info] The post ${postpath} is up-to-date, skipped.`);
      return {
        success: true,
        pageId: page.id,
        hugoPath: postpath,
        hash: (post.metadata as any).conversionHash,
      };
    }

    // Render and save the page
    console.info(`[Info] Updating ${postpath}`);
    const { title, pageString, hash } = await renderPage(page, notion);
    const fileName = getFileName(title, page.id);

    await sh(`hugo new "${mount.target_folder}/${fileName}"`, false);
    fs.writeFileSync(`content/${mount.target_folder}/${fileName}`, pageString);

    return {
      success: true,
      pageId: page.id,
      hugoPath: postpath,
      hash,
    };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      success: false,
      pageId: page.id,
      error: errorMessage,
    };
  }
}

export async function batchProcessPages(
  pages: PageObjectResponse[],
  notion: Client,
  mount: DatabaseMount | PageMount,
): Promise<BatchProcessResult> {
  const results: BatchProcessResult = {
    success: [],
    errors: [],
    skipped: [],
    timestamp: new Date().toISOString(),
    totalProcessed: 0,
  };

  for (const page of pages) {
    try {
      const result = await savePage(page, notion, mount);
      results.totalProcessed++;

      if (result.success) {
        if (result.hugoPath) {
          results.success.push(result);
        } else {
          results.skipped.push(result);
        }
      } else {
        results.errors.push(result);
      }
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      results.errors.push({
        success: false,
        pageId: page.id,
        error: errorMessage,
      });
    }
  }

  return results;
}
