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

export async function renderPage(page: PageObjectResponse, notion: Client) {
  // load formatter config
  const n2m = new NotionToMarkdown({ notionClient: notion });
  n2m.setUnsupportedTransformer((type) => {
    return `{{< notion-unsupported-block type=${type} >}}`;
  });
  let frontInjectString = "";
  let nearest_expiry_time: string | null = null;
  const mdblocks = await n2m.pageToMarkdown(page.id);
  const page_expiry_time = getExpiryTime(mdblocks);
  if (page_expiry_time) nearest_expiry_time = page_expiry_time;
  const mdString = n2m.toMarkdownString(mdblocks);
  page.properties.Name;
  const title = getPageTitle(page);

  // --- 변경된 부분: Published 속성 사용 --- //
  // Published 속성이 존재하고 올바른 날짜가 있다면 이를 date로 사용하고,
  // 그렇지 않으면 last_edited_time을 date로 사용합니다.
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

  const frontMatter: Record<
    string,
    string | string[] | number | boolean | PageObjectResponse
  > = {
    title,
    date: publishedDate,
    lastmod: page.last_edited_time,
    draft: false,
  };

  // set featuredImage
  const featuredImageLink = await getCoverLink(page.id, notion);
  if (featuredImageLink) {
    const { link, expiry_time } = featuredImageLink;
    frontMatter.featuredImage = link;
    // update nearest_expiry_time
    if (expiry_time) {
      if (nearest_expiry_time) {
        nearest_expiry_time =
          expiry_time < nearest_expiry_time ? expiry_time : nearest_expiry_time;
      } else {
        nearest_expiry_time = expiry_time;
      }
    }
  }

  let hasAuthor = false; // 작성자 정보 존재 여부 추적

  // map page properties to front matter
  for (const property in page.properties) {
    const id = page.properties[property].id;
    const response = await notion.pages.properties.retrieve({
      page_id: page.id,
      property_id: id,
    });
    if (response.object === "property_item") {
      switch (response.type) {
        case "checkbox":
          frontMatter[property] = response.checkbox;
          break;
        case "select":
          if (response.select) {
            frontMatter[property] = response.select.name;
            // Author 또는 작성자 관련 속성인 경우
            if (property.toLowerCase().includes("author")) {
              frontMatter.authors = [response.select.name];
              hasAuthor = true;
            }
          }
          break;
        case "multi_select":
          frontMatter[property] = response.multi_select.map(
            (select) => select.name,
          );
          // Author 또는 작성자 관련 속성인 경우
          if (property.toLowerCase().includes("author")) {
            frontMatter.authors = response.multi_select.map(
              (select) => select.name,
            );
            hasAuthor = true;
          }
          break;
        case "email":
          if (response.email) frontMatter[property] = response.email;
          break;
        case "url":
          if (response.url) frontMatter[property] = response.url;
          break;
        case "date":
          if (response.date) frontMatter[property] = response.date.start;
          break;
        case "number":
          if (response.number) frontMatter[property] = response.number;
          break;
        case "phone_number":
          if (response.phone_number)
            frontMatter[property] = response.phone_number;
          break;
        case "status":
          if (response.status) frontMatter[property] = response.status.name;
        // ignore these properties
        case "last_edited_by":
        case "last_edited_time":
        case "rollup":
        case "files":
        case "formula":
        case "created_by":
        case "created_time":
          break;
        default:
          break;
      }
    } else {
      for await (const result of iteratePaginatedAPI(
        // @ts-ignore
        notion.pages.properties.retrieve,
        {
          page_id: page.id,
          property_id: id,
        },
      )) {
        switch (result.type) {
          case "rich_text":
            frontMatter[property] = frontMatter[property] || "";
            frontMatter[property] += result.rich_text.plain_text;
            // Author 또는 작성자 관련 속성인 경우
            if (property.toLowerCase().includes("author")) {
              frontMatter.authors = [result.rich_text.plain_text];
              hasAuthor = true;
            }
            break;
          // ignore these
          case "relation":
          case "title":
          default:
            break;
        }
      }
    }
  }

  // 추가: 만약 Slug 속성이 존재하고 값이 있다면, frontMatter의 slug로 설정합니다.
  if (page.properties["Slug"] && page.properties["Slug"].type === "rich_text") {
    const slugProp = page.properties["Slug"];
    const slugValue = slugProp.rich_text.map(item => item.plain_text).join("").trim();
    if (slugValue) {
      frontMatter.slug = slugValue;
    }
  }

  // Subtitle 속성이 존재하면 subtitle 필드에 설정
  if (page.properties["Subtitle"] && page.properties["Subtitle"].type === "rich_text") {
    const subtitleProp = page.properties["Subtitle"];
    const subtitleValue = subtitleProp.rich_text.map(item => item.plain_text).join("").trim();
    if (subtitleValue) {
      frontMatter.subtitle = subtitleValue;
    }
  }
  
  // Description 속성이 존재하면 summary 필드에 설정
  if (page.properties["Description"] && page.properties["Description"].type === "rich_text") {
    const descriptionProp = page.properties["Description"];
    const descriptionValue = descriptionProp.rich_text.map(item => item.plain_text).join("").trim();
    if (descriptionValue) {
      frontMatter.summary = descriptionValue;
    }
  }
  
  // 작성자 정보가 없는 경우에만 기본값 설정
  if (!hasAuthor) {
    frontMatter.authors = ["Gunn Kim"];
  }

  // save metadata
  frontMatter.NOTION_METADATA = page;

  // save update time
  frontMatter.UPDATE_TIME = new Date().toISOString();
  // save nearest expiry time
  if (nearest_expiry_time) frontMatter.EXPIRY_TIME = nearest_expiry_time;

  return {
    title,
    pageString:
      "---\n" +
      YAML.stringify(frontMatter, {
        defaultStringType: "QUOTE_DOUBLE",
        defaultKeyType: "PLAIN",
      }) +
      "\n---\n" +
      frontInjectString +
      "\n" +
      mdString,
  };
}

export async function savePage(
  page: PageObjectResponse,
  notion: Client,
  mount: DatabaseMount | PageMount,
) {
  const postpath = path.join(
    "content",
    mount.target_folder,
    getFileName(getPageTitle(page), page.id),
  );
  const post = getContentFile(postpath);
  if (post) {
    const metadata = post.metadata;
    // if the page is not modified, continue
    if (
      post.expiry_time == null &&
      metadata.last_edited_time === page.last_edited_time
    ) {
      console.info(`[Info] The post ${postpath} is up-to-date, skipped.`);
      return;
    }
  }
  // otherwise update the page
  console.info(`[Info] Updating ${postpath}`);

  const { title, pageString } = await renderPage(page, notion);
  const fileName = getFileName(title, page.id);
  await sh(`hugo new "${mount.target_folder}/${fileName}"`, false);
  fs.writeFileSync(`content/${mount.target_folder}/${fileName}`, pageString);
}
