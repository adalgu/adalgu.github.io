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

async function hasProblematicContent(content, filePath) {
  // 문제가 되는 패턴들
  const patterns = [
    // 1. problematic shortcode 패턴
    {
      regex: /\[([^\]]+)\]\({{% relref "[^"]*"[^"]*" %}}(?:\))?/,
      type: "shortcode",
    },
    // 2. 잘못된 ref 링크 패턴
    {
      regex: /\[.*?\]\((.*?)\)/g,
      type: "ref",
      check: async (match) => {
        const refPath = match[1];
        if (!refPath.startsWith("http") && !refPath.startsWith("#")) {
          const targetPath = path.join(
            path.dirname(filePath),
            refPath.replace(/^\//, ""),
          );
          try {
            await fs.access(targetPath);
            return false; // 파일이 존재하면 문제 없음
          } catch {
            return true; // 파일이 없으면 문제 있음
          }
        }
        return false;
      },
    },
    // 3. {{< shortcode >}} 패턴 감지
    {
      regex: /{{<\s*([a-zA-Z0-9_-]+)\s*>}}/g,
      type: "shortcode",
      check: async (match, filePath) => {
        const shortcodeName = match[1];
        // 허용된 단축코드 목록
        const allowedShortcodes = [
          "youtube", "tweet", "video", "math", "notion-unsupported-block",
          // 테마에서 제공하는 단축코드들
          "collapse", "figure", "inTextImg", "ltr", "rawhtml", "rtl",
          // 추가한 단축코드
          "adsense2", "adfit"
        ];
        
        return !allowedShortcodes.includes(shortcodeName);
      }
    },
  ];

  for (const pattern of patterns) {
    if (pattern.type === "shortcode") {
      if (pattern.regex.test(content)) {
        // 기본 shortcode 패턴 (check 함수가 없는 경우)
        if (!pattern.check) {
          return {
            isProblematic: true,
            reason: "problematic_shortcode",
          };
        } else {
          // check 함수가 있는 경우 ({{< shortcode >}} 패턴)
          const matches = [...content.matchAll(pattern.regex)];
          for (const match of matches) {
            if (await pattern.check(match, filePath)) {
              return {
                isProblematic: true,
                reason: "problematic_shortcode",
              };
            }
          }
        }
      }
    } else if (pattern.type === "ref") {
      const matches = [...content.matchAll(pattern.regex)];
      for (const match of matches) {
        if (await pattern.check(match)) {
          return {
            isProblematic: true,
            reason: "ref_not_found",
          };
        }
      }
    }
  }

  return {
    isProblematic: false,
  };
}

async function processFile(filePath) {
  try {
    const content = await fs.readFile(filePath, "utf8");

    // 문제가 있는 파일인지 검사
    const { isProblematic, reason } = await hasProblematicContent(
      content,
      filePath,
    );

    if (isProblematic) {
      // problematic 디렉토리 생성 (프로젝트 루트에)
      const problematicDir = path.join(
        "problematic",
        reason === "ref_not_found" ? "ref_errors" : "shortcode_errors",
      );
      await fs.mkdir(problematicDir, { recursive: true });

      // 파일을 problematic 디렉토리로 이동
      const fileName = path.basename(filePath);
      const newPath = path.join(problematicDir, fileName);
      await fs.writeFile(newPath, content, "utf8");

      // 원본 파일 삭제
      await fs.unlink(filePath);

      console.log(
        `Problematic file moved (${reason}): ${filePath} -> ${newPath}`,
      );
      return {
        processed: true,
        reason,
      };
    }

    return {
      processed: false,
    };
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error);
    return {
      processed: false,
    };
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

    let shortcodeErrors = 0;
    let refErrors = 0;
    let processedCount = 0;

    for (const file of allFiles) {
      const { processed, reason } = await processFile(file);
      if (processed) {
        if (reason === "ref_not_found") {
          refErrors++;
        } else {
          shortcodeErrors++;
        }
      }
      processedCount++;
    }

    console.log("\nProcessing Summary:");
    console.log(`Total files processed: ${processedCount}`);
    console.log(`Files with shortcode errors: ${shortcodeErrors}`);
    console.log(`Files with ref errors: ${refErrors}`);
    console.log(
      `Normal files remaining: ${
        processedCount - (shortcodeErrors + refErrors)
      }`,
    );
  } catch (error) {
    console.error("Error during preprocessing:", error);
    process.exit(1);
  }
}

main();
