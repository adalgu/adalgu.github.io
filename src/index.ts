import { Client, isFullPage, iteratePaginatedAPI } from "@notionhq/client";
import dotenv from "dotenv";
import fs from "fs-extra";
import { savePage, batchProcessPages } from "./render";
import { loadConfig } from "./config";
import { getAllContentFiles } from "./file";
import { isFullPageOrDatabase } from "@notionhq/client/build/src/helpers";
import { BatchProcessResult } from "./types";

dotenv.config();

async function processDatabases(
  notion: Client,
  config: any,
): Promise<{ pageIds: string[]; results: BatchProcessResult[] }> {
  const pageIds: string[] = [];
  const results: BatchProcessResult[] = [];

  console.info("[Info] Start processing mounted databases");
  for (const mount of config.mount.databases) {
    fs.ensureDirSync(`content/${mount.target_folder}`);
    const pages: any[] = [];

    for await (const page of iteratePaginatedAPI(notion.databases.query, {
      database_id: mount.database_id,
    })) {
      if (!isFullPageOrDatabase(page) || page.object !== "page") {
        continue;
      }
      pages.push(page);
      pageIds.push(page.id);
    }

    if (pages.length > 0) {
      console.info(
        `[Info] Processing ${pages.length} pages from database ${mount.database_id}`,
      );
      const result = await batchProcessPages(pages, notion, mount);
      results.push(result);
    }
  }

  return { pageIds, results };
}

async function processPages(
  notion: Client,
  config: any,
): Promise<{ pageIds: string[]; results: BatchProcessResult[] }> {
  const pageIds: string[] = [];
  const results: BatchProcessResult[] = [];

  console.info("[Info] Start processing mounted pages");
  for (const mount of config.mount.pages) {
    const page = await notion.pages.retrieve({ page_id: mount.page_id });
    if (!isFullPage(page)) continue;
    pageIds.push(page.id);

    const result = await batchProcessPages([page], notion, mount);
    results.push(result);
  }

  return { pageIds, results };
}

async function cleanupOrphanedFiles(pageIds: string[]): Promise<void> {
  console.info("[Info] Checking for orphaned files");
  console.info(`[Debug] Current page IDs: ${pageIds.join(", ")}`);

  const contentFiles = getAllContentFiles("content");
  let removedCount = 0;

  for (const file of contentFiles) {
    const fileId = file.metadata.id;
    console.info(`[Debug] Checking file: ${file.filepath} with ID: ${fileId}`);

    // Skip files that are still being processed
    if (pageIds.includes(fileId)) {
      console.info(`[Debug] File ${file.filepath} is still active`);
      continue;
    }

    // Skip files without proper metadata
    if (!fileId) {
      console.warn(
        `[Warn] File ${file.filepath} has no valid ID, skipping cleanup`,
      );
      continue;
    }

    console.info(`[Info] Removing orphaned file: ${file.filepath}`);
    fs.removeSync(file.filepath);
    removedCount++;
  }

  if (removedCount > 0) {
    console.info(`[Info] Removed ${removedCount} orphaned files`);
  } else {
    console.info("[Info] No orphaned files found");
  }
}

function printResults(results: BatchProcessResult[]): void {
  const totals = results.reduce(
    (acc, result) => {
      acc.processed += result.totalProcessed;
      acc.success += result.success.length;
      acc.errors += result.errors.length;
      acc.skipped += result.skipped.length;
      return acc;
    },
    { processed: 0, success: 0, errors: 0, skipped: 0 },
  );

  console.info("\n=== Conversion Summary ===");
  console.info(`Total Processed: ${totals.processed}`);
  console.info(`Successful: ${totals.success}`);
  console.info(`Skipped: ${totals.skipped}`);
  console.info(`Errors: ${totals.errors}`);

  if (totals.errors > 0) {
    console.error("\nErrors encountered:");
    results.forEach((result) => {
      result.errors.forEach((error) => {
        console.error(`- Page ${error.pageId}: ${error.error}`);
      });
    });
  }
}

async function main() {
  try {
    if (!process.env.NOTION_TOKEN) {
      throw new Error("NOTION_TOKEN environment variable is not set");
    }

    const config = await loadConfig();
    console.info("[Info] Config loaded");

    const notion = new Client({
      auth: process.env.NOTION_TOKEN,
    });

    // Process databases and pages
    const dbResults = await processDatabases(notion, config);
    const pageResults = await processPages(notion, config);

    // Combine all page IDs and results
    const allPageIds = [...dbResults.pageIds, ...pageResults.pageIds];
    const allResults = [...dbResults.results, ...pageResults.results];

    // Clean up orphaned files
    await cleanupOrphanedFiles(allPageIds);

    // Print summary
    printResults(allResults);

    // Exit with error if any conversions failed
    const hasErrors = allResults.some((result) => result.errors.length > 0);
    if (hasErrors) {
      process.exit(1);
    }
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`[Error] ${errorMessage}`);
    process.exit(1);
  }
}

main().catch((error) => {
  console.error("[Fatal Error]", error);
  process.exit(1);
});
