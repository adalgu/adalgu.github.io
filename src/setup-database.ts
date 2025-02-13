import dotenv from "dotenv";
import fs from "fs";
import { NotionHugoDatabaseSetup, NotionSetupConfig } from "./utils/setup";

dotenv.config();

async function updateConfig(databaseId: string, targetFolder: string) {
  const configContent = `import { defineConfig } from "./src/config";

export default defineConfig({
  mount: {
    manual: true,
    databases: [
      {
        database_id: "${databaseId}",
        target_folder: "${targetFolder}"
      }
    ]
  }
});
`;

  fs.writeFileSync("notion-hugo.config.ts", configContent);
  console.info("Updated notion-hugo.config.ts with new database configuration");
}

async function main() {
  // Get configuration from command line arguments or environment variables
  const parentPageId = process.argv[2];
  const databaseName = process.argv[3] || "Hugo Blog Posts";
  const targetFolder = process.argv[4] || "posts";
  const notionToken = process.env.NOTION_TOKEN;

  if (!parentPageId) {
    console.error("Error: Parent page ID is required");
    console.error(
      "Usage: npm run setup-database <parent-page-id> [database-name] [target-folder]",
    );
    process.exit(1);
  }

  if (!notionToken) {
    console.error("Error: NOTION_TOKEN environment variable is not set");
    process.exit(1);
  }

  const config: NotionSetupConfig = {
    parentPageId,
    databaseName,
    notionToken,
  };

  const setup = new NotionHugoDatabaseSetup(config);

  try {
    console.info("Creating Hugo database...");
    const database = await setup.createHugoDatabase();
    console.info("Database created successfully:", database.id);

    console.info("Creating sample post...");
    await setup.createSamplePost(database.id);
    console.info("Setup completed successfully!");

    // Update configuration file
    await updateConfig(database.id, targetFolder);

    console.info("\nSetup completed!");
    console.info(
      "1. Open the database in Notion:",
      `https://notion.so/${database.id.replace(/-/g, "")}`,
    );
    console.info("2. Configuration has been updated automatically");
    console.info("3. Run 'npm start' to begin syncing your posts");
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Setup failed:", errorMessage);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
