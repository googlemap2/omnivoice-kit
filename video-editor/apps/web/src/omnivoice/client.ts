export const OMNIVOICE_API_BASE_URL_STORAGE_KEY = "omnivoice.apiBaseUrl";
export const DEFAULT_OMNIVOICE_API_BASE_URL = "http://127.0.0.1:8000";
export const DEFAULT_TRANSCRIPTION_MODEL = "Systran/faster-whisper-large-v3";

export function getOmniVoiceApiBaseUrl() {
	if (typeof window === "undefined") return DEFAULT_OMNIVOICE_API_BASE_URL;

	return (
		window.localStorage.getItem(OMNIVOICE_API_BASE_URL_STORAGE_KEY) ??
		DEFAULT_OMNIVOICE_API_BASE_URL
	);
}

function normalizeBaseUrl(value: string) {
	const trimmed = value.trim();
	return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

async function omniVoiceFetch(
	baseUrl: string,
	path: string,
	init?: RequestInit,
) {
	const response = await fetch(`${normalizeBaseUrl(baseUrl)}${path}`, {
		...init,
		headers: {
			"ngrok-skip-browser-warning": "true",
			...init?.headers,
		},
	});

	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || `OmniVoice request failed: ${response.status}`);
	}

	return response;
}

export async function transcribeWithOmniVoice({
	apiBaseUrl,
	file,
	model,
	language,
	translate,
	targetLanguage,
}: {
	apiBaseUrl: string;
	file: File;
	model: string;
	language: string;
	translate: boolean;
	targetLanguage: string;
}) {
	const formData = new FormData();
	formData.append("file", file);
	formData.append("model", model);
	formData.append("response_format", "srt");
	formData.append("word_timestamps", "true");
	formData.append("translate", String(translate));

	if (language !== "auto") {
		formData.append("language", language);
	}

	if (translate) {
		formData.append("target_language", targetLanguage);
	}

	const response = await omniVoiceFetch(
		apiBaseUrl,
		"/v1/audio/transcriptions",
		{
			method: "POST",
			body: formData,
		},
	);

	return response.text();
}
