import { defineConfig } from "./src/config";

export default defineConfig({
  mount: {
    manual: true,
    databases: [
      {
        database_id: "eb897916879243289a3612c1b793c43f",
        target_folder: "posts",
      },
    ],
  },
});
