import { PageObjectResponse } from "@notionhq/client/build/src/api-endpoints";

export interface NotionToHugoMapping {
  // Required Properties
  title: string;
  draft?: boolean;
  description: string;
  tags: string[];
  date: string;
  lastmod: string;

  // Optional Properties
  author?: string;
  cover?: {
    image?: string;
    alt?: string;
    caption?: string;
  };
  showToc?: boolean;
  hideSummary?: boolean;
  featured?: boolean;
  subtitle?: string;

  // Hugo Default Settings
  TocOpen: boolean;
  disableShare: boolean;
  ShowReadingTime: boolean;
  ShowBreadCrumbs: boolean;
  ShowPostNavLinks: boolean;
  UseHugoToc: boolean;

  // Automation Tracking
  NOTION_METADATA: {
    id: string;
    convertedToHugo: boolean;
    lastConvertedAt: string;
    conversionHash: string;
    conversionError?: string;
    needsReview: boolean;
    hugoPath: string;
  };
}

export interface ConversionResult {
  success: boolean;
  pageId: string;
  hugoPath?: string;
  error?: string;
  hash?: string;
}

export interface BatchProcessResult {
  success: ConversionResult[];
  errors: ConversionResult[];
  skipped: ConversionResult[];
  timestamp: string;
  totalProcessed: number;
}

export const DEFAULT_HUGO_SETTINGS = {
  showToc: true,
  TocOpen: false,
  disableShare: false,
  ShowReadingTime: true,
  ShowBreadCrumbs: true,
  ShowPostNavLinks: true,
  UseHugoToc: true,
};

export const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB
