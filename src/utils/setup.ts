import { Client } from "@notionhq/client";

export interface NotionSetupConfig {
  parentPageId: string;
  databaseName: string;
  notionToken: string;
}

export class NotionHugoDatabaseSetup {
  private notion: Client;
  private config: NotionSetupConfig;

  constructor(config: NotionSetupConfig) {
    this.notion = new Client({ auth: config.notionToken });
    this.config = config;
  }

  async createHugoDatabase() {
    try {
      // Create the database
      const database = await this.notion.databases.create({
        parent: {
          type: "page_id",
          page_id: this.config.parentPageId,
        },
        title: [
          {
            type: "text",
            text: { content: this.config.databaseName },
          },
        ],
        properties: {
          // Required Properties
          Name: {
            title: {},
          },
          Slug: {
            type: "rich_text",
            rich_text: {},
          },
          isPublished: {
            type: "checkbox",
            checkbox: {},
          },
          Description: {
            type: "rich_text",
            rich_text: {},
          },
          Tags: {
            type: "multi_select",
            multi_select: {
              options: [
                { name: "tech", color: "blue" },
                { name: "life", color: "green" },
                { name: "dev", color: "red" },
              ],
            },
          },
          "Created time": {
            type: "date",
            date: {},
          },
          "Last Updated": {
            type: "last_edited_time",
            last_edited_time: {},
          },

          // Optional Properties
          Author: {
            type: "rich_text",
            rich_text: {},
          },
          Cover: {
            type: "files",
            files: {},
          },
          ShowToc: {
            type: "checkbox",
            checkbox: {},
          },
          HideSummary: {
            type: "checkbox",
            checkbox: {},
          },
          isFeatured: {
            type: "checkbox",
            checkbox: {},
          },
          Subtitle: {
            type: "rich_text",
            rich_text: {},
          },

          // Automation Properties
          convertedToHugo: {
            type: "checkbox",
            checkbox: {},
          },
          lastConvertedAt: {
            type: "date",
            date: {},
          },
          conversionHash: {
            type: "rich_text",
            rich_text: {},
          },
          conversionError: {
            type: "rich_text",
            rich_text: {},
          },
          needsReview: {
            type: "checkbox",
            checkbox: {},
          },
          hugoPath: {
            type: "rich_text",
            rich_text: {},
          },
        },
      });

      // Create views
      await this.createCustomViews(database.id);

      return database;
    } catch (error) {
      console.error("Failed to create Hugo database:", error);
      throw error;
    }
  }

  private async createCustomViews(databaseId: string) {
    const views = [
      {
        name: "📝 All Posts",
        filter: {},
        sort: [
          {
            property: "Last Updated",
            direction: "descending",
          },
        ],
      },
      {
        name: "✅ Published",
        filter: {
          property: "isPublished",
          checkbox: {
            equals: true,
          },
        },
      },
      {
        name: "📋 Drafts",
        filter: {
          property: "isPublished",
          checkbox: {
            equals: false,
          },
        },
      },
      {
        name: "⚠️ Needs Review",
        filter: {
          property: "needsReview",
          checkbox: {
            equals: true,
          },
        },
      },
      {
        name: "❌ Conversion Errors",
        filter: {
          property: "conversionError",
          rich_text: {
            is_not_empty: true,
          },
        },
      },
    ];

    for (const view of views) {
      try {
        await this.notion.databases.update({
          database_id: databaseId,
          ...view,
        });
      } catch (error) {
        console.warn(`Failed to create view "${view.name}":`, error);
      }
    }
  }

  async createSamplePost(databaseId: string) {
    try {
      await this.notion.pages.create({
        parent: {
          database_id: databaseId,
        },
        properties: {
          Name: {
            title: [
              {
                type: "text",
                text: {
                  content: "Welcome to My Hugo Blog",
                },
              },
            ],
          },
          Slug: {
            type: "rich_text",
            rich_text: [
              {
                type: "text",
                text: {
                  content: "welcome-to-my-hugo-blog",
                },
              },
            ],
          },
          isPublished: {
            type: "checkbox",
            checkbox: false,
          },
          Description: {
            type: "rich_text",
            rich_text: [
              {
                type: "text",
                text: {
                  content:
                    "This is a sample post created automatically. Feel free to edit or delete it.",
                },
              },
            ],
          },
          Tags: {
            type: "multi_select",
            multi_select: [{ name: "tech" }],
          },
          ShowToc: {
            type: "checkbox",
            checkbox: true,
          },
          isFeatured: {
            type: "checkbox",
            checkbox: false,
          },
          Subtitle: {
            type: "rich_text",
            rich_text: [
              {
                type: "text",
                text: {
                  content:
                    "A sample post demonstrating Notion to Hugo conversion",
                },
              },
            ],
          },
          Author: {
            type: "rich_text",
            rich_text: [
              {
                type: "text",
                text: {
                  content: "Blog Owner",
                },
              },
            ],
          },
          "Created time": {
            type: "date",
            date: {
              start: new Date().toISOString(),
            },
          },
        },
        children: [
          {
            object: "block",
            type: "heading_1",
            heading_1: {
              rich_text: [
                { type: "text", text: { content: "Welcome to My Hugo Blog" } },
              ],
            },
          },
          {
            object: "block",
            type: "paragraph",
            paragraph: {
              rich_text: [
                {
                  type: "text",
                  text: {
                    content:
                      "This is a sample post that demonstrates various Notion block types that will be converted to Hugo markdown.",
                  },
                },
              ],
            },
          },
          {
            object: "block",
            type: "heading_2",
            heading_2: {
              rich_text: [
                { type: "text", text: { content: "Text Formatting" } },
              ],
            },
          },
          {
            object: "block",
            type: "paragraph",
            paragraph: {
              rich_text: [
                {
                  type: "text",
                  text: { content: "You can use " },
                },
                {
                  type: "text",
                  text: { content: "bold" },
                  annotations: { bold: true },
                },
                {
                  type: "text",
                  text: { content: ", " },
                },
                {
                  type: "text",
                  text: { content: "italic" },
                  annotations: { italic: true },
                },
                {
                  type: "text",
                  text: { content: ", and " },
                },
                {
                  type: "text",
                  text: { content: "code" },
                  annotations: { code: true },
                },
                {
                  type: "text",
                  text: { content: " formatting." },
                },
              ],
            },
          },
          {
            object: "block",
            type: "heading_2",
            heading_2: {
              rich_text: [{ type: "text", text: { content: "Lists" } }],
            },
          },
          {
            object: "block",
            type: "bulleted_list_item",
            bulleted_list_item: {
              rich_text: [
                { type: "text", text: { content: "Unordered list item 1" } },
              ],
            },
          },
          {
            object: "block",
            type: "bulleted_list_item",
            bulleted_list_item: {
              rich_text: [
                { type: "text", text: { content: "Unordered list item 2" } },
              ],
            },
          },
          {
            object: "block",
            type: "numbered_list_item",
            numbered_list_item: {
              rich_text: [
                { type: "text", text: { content: "Ordered list item 1" } },
              ],
            },
          },
          {
            object: "block",
            type: "numbered_list_item",
            numbered_list_item: {
              rich_text: [
                { type: "text", text: { content: "Ordered list item 2" } },
              ],
            },
          },
          {
            object: "block",
            type: "heading_2",
            heading_2: {
              rich_text: [{ type: "text", text: { content: "Code Block" } }],
            },
          },
          {
            object: "block",
            type: "code",
            code: {
              language: "typescript",
              rich_text: [
                {
                  type: "text",
                  text: {
                    content: 'console.log("Hello from Hugo!");',
                  },
                },
              ],
            },
          },
          {
            object: "block",
            type: "heading_2",
            heading_2: {
              rich_text: [{ type: "text", text: { content: "Quote" } }],
            },
          },
          {
            object: "block",
            type: "quote",
            quote: {
              rich_text: [
                {
                  type: "text",
                  text: {
                    content:
                      "This is a quote block that will be properly formatted in Hugo.",
                  },
                },
              ],
            },
          },
          {
            object: "block",
            type: "heading_2",
            heading_2: {
              rich_text: [{ type: "text", text: { content: "Callout" } }],
            },
          },
          {
            object: "block",
            type: "callout",
            callout: {
              rich_text: [
                {
                  type: "text",
                  text: {
                    content: "This is a callout block with an emoji.",
                  },
                },
              ],
              icon: {
                type: "emoji",
                emoji: "💡",
              },
            },
          },
        ],
      });
    } catch (error) {
      console.error("Failed to create sample post:", error);
      throw error;
    }
  }
}
