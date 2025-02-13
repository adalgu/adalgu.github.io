import { Client, isFullPage } from "@notionhq/client";
import { PageObjectResponse } from "@notionhq/client/build/src/api-endpoints";

export function getPageTitle(page: PageObjectResponse): string {
  const title = page.properties.Name ?? page.properties.title;
  if (title.type === "title") {
    return title.title.map((text) => text.plain_text).join("");
  }
  throw Error(
    `page.properties.Name has type ${title.type} instead of title. The underlying Notion API might has changed, please report an issue to the author.`,
  );
}

export async function getCoverLink(
  page_id: string,
  notion: Client,
): Promise<{ link: string; expiry_time: string | null } | null> {
  const page = await notion.pages.retrieve({ page_id });
  if (!isFullPage(page)) return null;
  if (page.cover === null) return null;
  if (page.cover.type === "external")
    return {
      link: page.cover.external.url,
      expiry_time: null,
    };
  else
    return {
      link: page.cover.file.url,
      expiry_time: page.cover.file.expiry_time,
    };
}

/**
 * 한글 문자 여부 확인
 */
function containsHangul(str: string): boolean {
  return /[\u3131-\u314e|\u314f-\u3163|\uac00-\ud7a3]/.test(str);
}

/**
 * 제목을 안전한 슬러그로 변환
 * - 이모티콘 및 특수 유니코드 제거
 * - 한글이 포함된 경우 처음 3단어는 그대로 두고, 나머지는 영문 소문자로 변환
 * - 최종적으로 영문, 숫자, 한글, 공백, 하이픈만 허용하고, 공백은 하이픈으로 변환
 */
function slugify(title: string): string {
  // 1. 이모티콘 및 특수 유니코드 제거
  const cleanTitle = title
    .replace(
      /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F000}-\u{1F02F}\u{1F0A0}-\u{1F0FF}\u{1F100}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F910}-\u{1F96B}\u{1F980}-\u{1F9E0}]/gu,
      "",
    )
    .trim();

  // 2. 한글이 포함된 경우 처음 3단어만 유지하고 나머지는 영문으로 변환
  if (containsHangul(cleanTitle)) {
    const words = cleanTitle.split(/\s+/).filter((word) => word.length > 0);
    const firstThreeWords = words.slice(0, 3).join(" ");
    const remainingWords = words.slice(3).join(" ");

    // 처음 3단어는 그대로, 나머지는 영문 소문자 처리
    let slug = firstThreeWords;
    if (remainingWords) {
      const normalizedRemaining = remainingWords
        .toLowerCase()
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^\x00-\x7F]/g, "");
      if (normalizedRemaining.trim()) {
        slug += " " + normalizedRemaining;
      }
    }

    // ★ 여기서 전체 슬러그를 소문자로 변환 (영문 대문자 문제 해결)
    slug = slug.toLowerCase();

    // 최종 슬러그 생성
    return slug
      .replace(/[^a-z0-9가-힣\s-]/g, "") // 허용된 문자만 남김
      .replace(/[\s_]+/g, "-") // 공백을 하이픈으로
      .replace(/-+/g, "-") // 중복 하이픈 제거
      .replace(/^-+|-+$/g, ""); // 시작/끝 하이픈 제거
  }

  // 3. 영문/기타 제목인 경우
  return cleanTitle
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s-]/g, "") // 영문, 숫자, 공백, 하이픈만 허용
    .replace(/[\s_]+/g, "-") // 공백을 하이픈으로
    .replace(/-+/g, "-") // 중복 하이픈 제거
    .replace(/^-+|-+$/g, ""); // 시작/끝 하이픈 제거
}

/**
 * 파일명 생성
 * - slugify로 안전한 문자열 생성
 * - 최대 길이 제한
 * - page_id 추가
 */
export function getFileName(title: string, page_id: string): string {
  // 1. 제목을 안전한 슬러그로 변환
  const slug = slugify(title);

  // 2. 파일명 길이 제한 (확장자 .md(3) + 하이픈(1) + page_id(32) = 36자 여유 확보)
  const MAX_TITLE_LENGTH = 180;
  const truncatedSlug = slug.slice(0, MAX_TITLE_LENGTH);

  // 3. page_id에서 하이픈 제거하고 파일명 생성
  const cleanPageId = page_id.replaceAll("-", "");

  return `${truncatedSlug}-${cleanPageId}.md`;
}
