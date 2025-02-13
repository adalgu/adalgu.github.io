import { createHash } from "crypto";
import { PageObjectResponse } from "@notionhq/client/build/src/api-endpoints";

export function calculateContentHash(page: PageObjectResponse): string {
  const contentToHash = {
    title: page.properties.Name,
    lastEdited: page.last_edited_time,
    isPublished: page.properties.isPublished,
    description: page.properties.Description,
    tags: page.properties.Tags,
  };

  return createHash("sha256")
    .update(JSON.stringify(contentToHash))
    .digest("hex");
}

export function hasContentChanged(
  page: PageObjectResponse,
  previousHash?: string,
): boolean {
  if (!previousHash) return true;

  const currentHash = calculateContentHash(page);
  return currentHash !== previousHash;
}
