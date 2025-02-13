const fs = require("fs").promises;
const path = require("path");

async function findMarkdownFiles(dir) {
  const files = await fs.readdir(dir);
  const markdownFiles = [];

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = await fs.stat(filePath);

    if (stat.isDirectory()) {
      const subDirFiles = await findMarkdownFiles(filePath);
      markdownFiles.push(...subDirFiles);
    } else if (file.endsWith(".md")) {
      markdownFiles.push(filePath);
    }
  }

  return markdownFiles;
}

async function hasProblematicShortcode(content) {
  // 문제가 되는 shortcode 패턴 검사
  const problematicPattern =
    /\[([^\]]+)\]\({{% relref "[^"]*"[^"]*" %}}(?:\))?/;
  return problematicPattern.test(content);
}

async function processFile(filePath) {
  try {
    const content = await fs.readFile(filePath, "utf8");

    // 문제가 있는 파일인지 검사
    const isProblematic = await hasProblematicShortcode(content);

    if (isProblematic) {
      // problematic 디렉토리 생성 (프로젝트 루트에)
      const problematicDir = "problematic";
      await fs.mkdir(problematicDir, { recursive: true });

      // 파일을 problematic 디렉토리로 이동
      const fileName = path.basename(filePath);
      const newPath = path.join(problematicDir, fileName);
      await fs.writeFile(newPath, content, "utf8");

      // 원본 파일 삭제
      await fs.unlink(filePath);

      console.log(`Problematic file moved: ${filePath} -> ${newPath}`);
      return true;
    }

    return false;
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error);
    return false;
  }
}

async function main() {
  try {
    // content/posts와 content/problematic 모두 검사
    const directories = [
      path.join("content", "posts"),
      path.join("content", "problematic"),
    ];

    let allFiles = [];
    for (const dir of directories) {
      try {
        const files = await findMarkdownFiles(dir);
        allFiles.push(...files);
      } catch (error) {
        // 디렉토리가 없으면 무시
        if (error.code !== "ENOENT") {
          throw error;
        }
      }
    }

    let problematicCount = 0;
    let processedCount = 0;

    for (const file of allFiles) {
      const isProblematic = await processFile(file);
      if (isProblematic) {
        problematicCount++;
      }
      processedCount++;
    }

    console.log("\nProcessing Summary:");
    console.log(`Total files processed: ${processedCount}`);
    console.log(`Problematic files moved: ${problematicCount}`);
    console.log(`Normal files remaining: ${processedCount - problematicCount}`);
  } catch (error) {
    console.error("Error during preprocessing:", error);
    process.exit(1);
  }
}

main();
