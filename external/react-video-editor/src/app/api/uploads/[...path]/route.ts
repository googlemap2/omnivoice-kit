import { mkdir, readFile, stat, writeFile } from "fs/promises";
import path from "path";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const uploadRoot = path.join(process.cwd(), ".local-uploads");

function getUploadPath(parts: string[]) {
  if (
    parts.length === 0 ||
    parts.some((part) => part === ".." || part.includes("\\") || part.includes("/"))
  ) {
    throw new Error("Invalid upload path");
  }

  return path.join(uploadRoot, ...parts);
}

function inferContentType(fileName: string) {
  const extension = fileName.split(".").pop()?.toLowerCase();

  switch (extension) {
    case "mp4":
      return "video/mp4";
    case "mov":
      return "video/quicktime";
    case "webm":
      return "video/webm";
    case "mp3":
      return "audio/mpeg";
    case "wav":
      return "audio/wav";
    case "m4a":
      return "audio/mp4";
    case "png":
      return "image/png";
    case "jpg":
    case "jpeg":
      return "image/jpeg";
    case "webp":
      return "image/webp";
    default:
      return "application/octet-stream";
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path: parts } = await params;
    const filePath = getUploadPath(parts);
    await mkdir(path.dirname(filePath), { recursive: true });
    await writeFile(filePath, Buffer.from(await request.arrayBuffer()));

    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to save upload",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 400 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const { path: parts } = await params;
    const filePath = getUploadPath(parts);
    const fileStat = await stat(filePath);
    const range = request.headers.get("range");
    const contentType = inferContentType(parts.at(-1) ?? "");

    if (range) {
      const match = range.match(/bytes=(\d+)-(\d*)/);
      const start = Number(match?.[1] ?? 0);
      const end = match?.[2] ? Number(match[2]) : fileStat.size - 1;
      const file = await readFile(filePath);
      const chunk = file.subarray(start, end + 1);

      return new NextResponse(chunk, {
        status: 206,
        headers: {
          "Accept-Ranges": "bytes",
          "Content-Length": String(chunk.length),
          "Content-Range": `bytes ${start}-${end}/${fileStat.size}`,
          "Content-Type": contentType
        }
      });
    }

    return new NextResponse(await readFile(filePath), {
      headers: {
        "Accept-Ranges": "bytes",
        "Content-Length": String(fileStat.size),
        "Content-Type": contentType
      }
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Upload not found",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 404 }
    );
  }
}
