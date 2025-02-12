import { UserConfig } from "./src/config";

const userConfig: UserConfig = {
  mount: {
    manual: false,
    page_url:
      // "https://www.notion.so/datarecipe/Notion-DoIt-1eafeafea06f4504a4a1a0d9e89fd2d5",
      "https://www.notion.so/datarecipe/Exobrain-f627c354dd9a4dfda25e39ed32a84fbd?pvs=4",
    pages: [
      // {
      //     page_id: '<page_id>',
      //     target_folder: 'path/relative/to/content/folder'
      // }
      {
        page_id: "1eafeafea06f4504a4a1a0d9e89fd2d5",
        target_folder: ".",
      },
    ],
    databases: [
      // {
      //     database_id: '<database_id>',
      //     target_folder: 'path/relative/to/content/folder'
      // }
      {
        database_id: "8229e4e434a647f7b098c86b7cd83ad6",
        target_folder: ".",
      },
      {
        database_id: "eb897916879243289a3612c1b793c43f",
        target_folder: "posts",
      },
    ],
  },
};

export default userConfig;
