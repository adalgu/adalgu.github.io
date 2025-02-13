import { Client, isFullPage } from "@notionhq/client";
import dotenv from "dotenv";
import { loadConfig } from "./config";
import { batchProcessPages } from "./render";
import { BatchProcessResult } from "./types";
import { PageMount } from "./config";

dotenv.config();

async function testConversion(pageId: string): Promise<void> {
  try {
    if (!process.env.NOTION_TOKEN) {
      throw new Error("NOTION_TOKEN environment variable is not set");
    }

    const notion = new Client({
      auth: process.env.NOTION_TOKEN,
    });

    // Retrieve the test page
    console.info("[Test] Retrieving test page");
    const page = await notion.pages.retrieve({ page_id: pageId });
    if (!isFullPage(page)) {
      throw new Error("Retrieved page is not a full page object");
    }

    // Process the page
    console.info("[Test] Converting page to Hugo format");
    const mount: PageMount = {
      page_id: pageId,
      target_folder: "test",
    };
    const result = await batchProcessPages([page], notion, mount);

    // Print results
    console.info("\n=== Test Results ===");
    if (result.success.length > 0) {
      console.info("[Success] Page converted successfully");
      console.info(`Output file: ${result.success[0].hugoPath}`);
    }

    if (result.errors.length > 0) {
      console.error("\n[Error] Conversion failed:");
      result.errors.forEach((error) => {
        console.error(`- ${error.error}`);
      });
      process.exit(1);
    }

    if (result.skipped.length > 0) {
      console.info("\n[Info] Page skipped (no changes detected)");
    }
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[Fatal Error] ${errorMessage}`);
    process.exit(1);
  }
}

// Get page ID from command line argument
const pageId = process.argv[2];
if (!pageId) {
  console.error("[Error] Please provide a page ID as an argument");
  console.error("Usage: npm run test-conversion <page-id>");
  process.exit(1);
}

testConversion(pageId);
