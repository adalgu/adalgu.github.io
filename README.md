# Notion-Hugo

![image](https://user-images.githubusercontent.com/52968553/188502839-1de28ae0-6111-4387-99fe-fbc7d87dbc4c.png)

Notion-Hugo allows you to use [Notion](https://www.notion.so/) as your CMS and deploy your pages as a static website with [Hugo](https://gohugo.io/). So you have the full power of Notion for creating new content, with Hugo and its wonderful [ecosystem of themes](https://themes.gohugo.io/) take care of the rest for you.

## Get Started

### Create a new GitHub repository from this template

Click the green "Use this template" button in the upper-right corner to create your repo from this template. Choose "public" for the repository visibility.

<picture>
  <source width="382" media="(prefers-color-scheme: light)" srcset="https://user-images.githubusercontent.com/52968553/188245872-0aa640e4-ea85-4fc7-8035-7a267b7a28a2.png">
  <source width="382" media="(prefers-color-scheme: dark)" srcset="https://user-images.githubusercontent.com/52968553/188245777-5b5d0e3d-b125-47cd-aa08-ed8e75f20773.png">
  <img width="382" alt="Use this template button" src="https://user-images.githubusercontent.com/52968553/188245777-5b5d0e3d-b125-47cd-aa08-ed8e75f20773.png">
</picture>

### Create a Notion integration

Visit [my integrations](https://www.notion.so/my-integrations) and login with your Notion account.

Click on "Create new integration" to create a new internal integration.

<img width="891" alt="Create new integration" src="https://user-images.githubusercontent.com/52968553/188289065-d2e3626e-d250-4d42-9fb4-8f641f4807ea.png">

In the capabilities section, select "Read Content" and "Read user information including email address". The "Read Content" permission is necessary for Notion-Hugo to pull your Notion content, and the "Read user information including email address" permission is used to fill front matters with author information. Notion-Hugo does not collect any of your information.

<img width="891" alt="Setup capabilities" src="https://user-images.githubusercontent.com/52968553/188289098-d318ebba-46a5-4d41-bfcd-ac0f09f35f82.png">

Click the submit button to finish creating the Notion integration.

### Setup secrets for GitHub Action

Copy the Internal Integration Token.

<img width="816" alt="Copy the Internal Integration Token" src="https://user-images.githubusercontent.com/52968553/188298208-23d96254-f8a7-4571-8863-0d920bb82143.png">

Navigate to the GitHub repo you just created, click on Settings -> Secrets -> Actions.

Click the "New Repository Secret" button on the top right.

<picture>
<source media="(prefers-color-scheme: light)" width="1148" srcset="https://user-images.githubusercontent.com/52968553/188298495-f4b1aa17-fff2-4b5e-adab-2aaddce22262.png">
<source media="(prefers-color-scheme: dark)" width="1148" srcset="https://user-images.githubusercontent.com/52968553/188298501-b479534e-db88-4c07-9e72-6bf9f9fd5a8d.png">
<img width="1148" alt="Setup secrets for GitHub Action" src="https://user-images.githubusercontent.com/52968553/188298495-f4b1aa17-fff2-4b5e-adab-2aaddce22262.png">
</picture>

Add a new secret with name `NOTION_TOKEN`, paste the copied token into the secret field. Click the green "Add secret" button to save the change.

<picture>
<source media="(prefers-color-scheme: light)" width="824" srcset="https://user-images.githubusercontent.com/52968553/188298507-5402a19f-dc35-45a9-b7b7-867f38cdb001.png">
<source media="(prefers-color-scheme: dark)" width="824" srcset="https://user-images.githubusercontent.com/52968553/188298515-3c98fbf3-128e-46ef-971f-b22b6d4da9e1.png">
<img width="824" alt="Add secret NOTION_TOKEN" src="https://user-images.githubusercontent.com/52968553/188298507-5402a19f-dc35-45a9-b7b7-867f38cdb001.png">
</picture>

### Setup Notion Database

You have two options to set up your Notion database:

#### Option 1: Use the Setup Script (Recommended)

Use the provided setup script to create a new database with all required properties:

```bash
npm run setup-database <parent-page-id> [database-name] [target-folder]
```

Parameters:

- `parent-page-id`: (Required) The Notion page ID where the database will be created
- `database-name`: (Optional) Name for the database (default: "Hugo Blog Posts")
- `target-folder`: (Optional) Folder for markdown files (default: "posts")

The script will:

1. Create a new database with all necessary properties
2. Create a sample post
3. Automatically update notion-hugo.config.ts
4. Provide a link to view the database

#### Option 2: Migrate Existing Database

If you already have a Notion database with blog posts, you can migrate it to the new structure:

```bash
npm run migrate-database <source-db-id> <parent-page-id> [target-folder]
```

Parameters:

- `source-db-id`: (Required) Your existing Notion database ID
- `parent-page-id`: (Required) The page ID where the new database will be created
- `target-folder`: (Optional) Folder for markdown files (default: "posts")

The migration script will:

1. Create a new database with our enhanced structure
2. Copy all content and properties from your existing database
3. Map existing properties to the new schema
4. Automatically update notion-hugo.config.ts
5. Preserve all your content and formatting

The script will validate your source database before migration:

- Checks for required properties (Name, isPublished, Description, etc.)
- Verifies property types match expected types
- Provides detailed error messages for any issues

Example validation output:

```
Database validation failed:

Missing required properties:
- Description
- Tags

Incompatible property types:
- isPublished: expected checkbox, found text
```

If validation fails:

1. Add any missing required properties to your source database
2. Correct property types to match expected types
3. Run the migration command again

#### Option 3: Duplicate Template

Alternatively, you can duplicate this [Notion Template](https://pcloud.notion.site/Notion-DoIt-04bcc51cfe4c49938229c35e4f0a6fb6) into your own workspace.

### Database Properties

The Notion database supports the following properties:

#### Required Properties

- `Name` (title): Post title
- `isPublished` (checkbox): Draft status
- `Description` (text): Post description/summary
- `Tags` (multi-select): Post tags
- `Created time` (date/created_time): Publication date (accepts both date and created_time types)
- `Last Updated` (last_edited_time/date): Last modification date (accepts both last_edited_time and date types)

#### Optional Properties

- `Slug` (text): Custom URL slug (auto-generated from title if not provided)
- `Author` (text): Post author (defaults to "Gunn Kim")
- `Cover` (files): Post cover image
- `ShowToc` (checkbox): Show table of contents
- `HideSummary` (checkbox): Hide post summary
- `isFeatured` (checkbox): Mark post as featured
- `Subtitle` (text): Post subtitle

The script will validate your source database before migration:

- Checks for required properties
- Verifies property types match expected types
- Provides detailed error messages for any issues
- Flexibly handles time-related properties (accepts multiple valid types)

Example validation output:

```
Database validation failed:

Missing required properties:
- Description
- Tags

Incompatible property types:
- isPublished: expected checkbox, found text
```

Note: Time-related properties (`Created time` and `Last Updated`) are handled flexibly:

- `Created time` accepts both `date` and `created_time` types
- `Last Updated` accepts both `last_edited_time` and `date` types
- The migration will automatically handle the conversion between these types

If validation fails:

1. Add any missing required properties to your source database
2. Correct property types to match expected types
3. Run the migration command again

[Rest of the original content remains the same...]

## FAQ

### Will the notion-hugo blog be synced with me Notion?

Yes. By default, the notion-hugo blog will be re-generated every 1 hour through `CD` action in Github Actions. You can change this in `.github/workflows/cd.yml` using `cron` option:

```
name: CD

on:
  ...

  schedule:
    - cron: '0 * * * *' # run every hour
```

Be aware that Github will allow you to re-run the job no more often than once per 5 minutes.

### What if I want to re-deploy immediately as Notion database updates?

This repo at the moment supports only cron option.

But, as an idea or direction - you could look for ways to listen for updates in Notion database and trigger Github Action when Notion database is updated. Usually webhooks are used for that purpose - but at the moment Notion has no official webhook support. So you would need to find a work around.
