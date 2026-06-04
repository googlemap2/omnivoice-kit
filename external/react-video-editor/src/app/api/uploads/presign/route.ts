import { NextRequest, NextResponse } from "next/server";

interface PresignRequest {
  userId: string;
  fileNames: string[];
}

interface ExternalPresignResponse {
  fileName: string;
  filePath: string;
  contentType: string;
  presignedUrl: string;
  folder?: string;
  url: string;
}

interface ExternalPresignsResponse {
  uploads: ExternalPresignResponse[];
}

const externalUploadServiceUrl = process.env.UPLOAD_SERVICE_URL;

function sanitizeFileName(fileName: string) {
  return fileName.replace(/[^\w.\-()[\] ]+/g, "_").replace(/\s+/g, "_");
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

export async function POST(request: NextRequest) {
  try {
    const body: PresignRequest = await request.json();
    const { userId, fileNames } = body;

    if (!userId) {
      return NextResponse.json(
        { error: "userId is required" },
        { status: 400 }
      );
    }

    if (!fileNames || !Array.isArray(fileNames) || fileNames.length === 0) {
      return NextResponse.json(
        { error: "fileNames array is required and must not be empty" },
        { status: 400 }
      );
    }

    if (!externalUploadServiceUrl) {
      const origin = request.headers.get("origin") ?? request.nextUrl.origin;
      const folder = `local/${userId}`;

      return NextResponse.json({
        success: true,
        uploads: fileNames.map((fileName) => {
          const safeName = sanitizeFileName(fileName);
          const filePath = `${folder}/${Date.now()}-${safeName}`;
          const url = `${origin}/api/uploads/${filePath}`;

          return {
            fileName,
            filePath,
            contentType: inferContentType(fileName),
            presignedUrl: url,
            folder,
            url
          };
        })
      });
    }

    // Call external presigned URL service
    const externalResponse = await fetch(`${externalUploadServiceUrl}/presigned`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        userId,
        fileNames
      })
    });

    if (!externalResponse.ok) {
      const errorData = await externalResponse.json();
      return NextResponse.json(
        {
          error: "External presigned URL service failed",
          details: errorData
        },
        { status: externalResponse.status }
      );
    }

    const externalData: ExternalPresignsResponse =
      await externalResponse.json();
    const { uploads = [] } = externalData;

    return NextResponse.json({
      success: true,
      uploads: uploads
    });
  } catch (error) {
    console.error("Error in presign route:", error);
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}
