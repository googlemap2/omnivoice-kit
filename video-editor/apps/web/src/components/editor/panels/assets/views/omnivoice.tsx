"use client";

import { useEffect, useReducer, useState } from "react";
import { Button } from "@/components/ui/button";
import { PanelView } from "@/components/editor/panels/assets/views/base-panel";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
	Section,
	SectionContent,
	SectionField,
	SectionFields,
} from "@/components/section";
import { Spinner } from "@/components/ui/spinner";
import { useEditor } from "@/hooks/use-editor";
import { extractTimelineAudio } from "@/lib/media/mediabunny";
import { insertCaptionChunksAsTextTrack } from "@/lib/subtitles/insert";
import { parseSubtitleFile } from "@/lib/subtitles/parse";
import { TRANSCRIPTION_LANGUAGES } from "@/lib/transcription/supported-languages";
import type { TranscriptionLanguage } from "@/lib/transcription/types";
import {
	DEFAULT_TRANSCRIPTION_MODEL,
	getOmniVoiceApiBaseUrl,
	transcribeWithOmniVoice,
	fetchTranscriptionModels,
	type TranscriptionModel,
} from "@/omnivoice/client";

type OmniVoiceViewTab = "transcript" | "tts";

type ProcessingState =
	| { status: "idle"; error: string | null; message: string | null }
	| { status: "processing"; step: string };

type ProcessingAction =
	| { type: "start"; step: string }
	| { type: "update_step"; step: string }
	| { type: "succeed"; message: string }
	| { type: "fail"; error: string };

const IDLE_STATE: ProcessingState = {
	status: "idle",
	error: null,
	message: null,
};

function processingReducer(
	state: ProcessingState,
	action: ProcessingAction,
): ProcessingState {
	switch (action.type) {
		case "start":
			return { status: "processing", step: action.step };
		case "update_step":
			if (state.status !== "processing") return state;
			return { status: "processing", step: action.step };
		case "succeed":
			return { status: "idle", error: null, message: action.message };
		case "fail":
			return { status: "idle", error: action.error, message: null };
	}
}

export function OmniVoiceView() {
	const [view, setView] = useState<OmniVoiceViewTab>("transcript");

	return (
		<PanelView title="OmniVoice" contentClassName="px-0 flex flex-col h-full">
			<div className="px-0 pt-0 flex h-full flex-col">
				<div className="px-3.5 pt-3">
					<Tabs value={view} onValueChange={(value) => setView(value as OmniVoiceViewTab)}>
						<TabsList>
							<TabsTrigger value="transcript">Transcript</TabsTrigger>
							<TabsTrigger value="tts">TTS</TabsTrigger>
						</TabsList>
					</Tabs>
				</div>
				<div className="flex-1 overflow-hidden">
					{view === "transcript" && <OmniVoiceTranscriptTab />}
					{view === "tts" && <OmniVoiceTtsTab />}
				</div>
			</div>
		</PanelView>
	);
}

function OmniVoiceTranscriptTab() {
	const editor = useEditor();
	const [apiBaseUrl] = useState(getOmniVoiceApiBaseUrl);
	const [model, setModel] = useState(DEFAULT_TRANSCRIPTION_MODEL);
	const [transcriptionModels, setTranscriptionModels] = useState<TranscriptionModel[]>([]);
	const [modelsLoading, setModelsLoading] = useState(true);
	const [selectedLanguage, setSelectedLanguage] =
		useState<TranscriptionLanguage>("auto");
	const [translate, setTranslate] = useState(false);
	const [targetLanguage, setTargetLanguage] = useState("en");
	const [processing, dispatch] = useReducer(processingReducer, IDLE_STATE);

	const isProcessing = processing.status === "processing";
	const error = processing.status === "idle" ? processing.error : null;
	const message = processing.status === "idle" ? processing.message : null;

	useEffect(() => {
		let cancelled = false;
		setModelsLoading(true);
		fetchTranscriptionModels(apiBaseUrl)
			.then((models) => {
				if (!cancelled) {
					setTranscriptionModels(models);
					if (models.length > 0 && model === DEFAULT_TRANSCRIPTION_MODEL) {
						setModel(models[0].id);
					}
				}
			})
			.catch((err) => {
				console.error("Failed to fetch transcription models:", err);
			})
			.finally(() => {
				if (!cancelled) setModelsLoading(false);
			});
		return () => {
			cancelled = true;
		};
	}, [apiBaseUrl]);

	const handleLanguageChange = ({ value }: { value: string }) => {
		if (value === "auto") {
			setSelectedLanguage("auto");
			return;
		}

		const matchedLanguage = TRANSCRIPTION_LANGUAGES.find(
			(language) => language.code === value,
		);
		if (!matchedLanguage) return;
		setSelectedLanguage(matchedLanguage.code);
	};

	const handleTranscribeTimeline = async () => {
		dispatch({ type: "start", step: "Extracting timeline audio..." });

		try {
			const audioBlob = await extractTimelineAudio({
				tracks: editor.scenes.getActiveScene().tracks,
				mediaAssets: editor.media.getAssets(),
				totalDuration: editor.timeline.getTotalDuration(),
			});

			const audioFile = new File([audioBlob], "timeline-audio.wav", {
				type: audioBlob.type || "audio/wav",
			});

			dispatch({ type: "update_step", step: "Calling OmniVoice backend..." });
			const srt = await transcribeWithOmniVoice({
				apiBaseUrl,
				file: audioFile,
				model,
				language: selectedLanguage,
				translate,
				targetLanguage,
			});

			dispatch({ type: "update_step", step: "Importing captions..." });
			const result = parseSubtitleFile({
				fileName: "omnivoice.srt",
				input: srt,
			});

			if (result.captions.length === 0) {
				dispatch({
					type: "fail",
					error: "OmniVoice returned no valid captions",
				});
				return;
			}

			const trackId = insertCaptionChunksAsTextTrack({
				editor,
				captions: result.captions,
			});

			if (!trackId) {
				dispatch({ type: "fail", error: "No captions were inserted" });
				return;
			}

			dispatch({
				type: "succeed",
				message: `Inserted ${result.captions.length} caption(s) from OmniVoice`,
			});
		} catch (error) {
			console.error("OmniVoice transcription failed:", error);
			dispatch({
				type: "fail",
				error:
					error instanceof Error
						? error.message
						: "An unexpected error occurred",
			});
		}
	};

	return (
		<Section showTopBorder={false} showBottomBorder={false} className="flex-1">
			<SectionContent className="flex flex-col gap-4 h-full pt-1">
				<SectionFields>
					<SectionField label="Transcription model">
						<Select
							value={model}
							onValueChange={setModel}
							disabled={modelsLoading}
						>
							<SelectTrigger>
								<SelectValue placeholder={modelsLoading ? "Loading models..." : "Select a model"} />
							</SelectTrigger>
							<SelectContent>
								{transcriptionModels.map((m) => (
									<SelectItem key={m.id} value={m.id}>
										{m.display_name}
									</SelectItem>
								))}
								{transcriptionModels.length === 0 && !modelsLoading && (
									<SelectItem value={DEFAULT_TRANSCRIPTION_MODEL} disabled>
										No models available
									</SelectItem>
								)}
							</SelectContent>
						</Select>
					</SectionField>
					<SectionField label="Language">
						<Select
							value={selectedLanguage}
							onValueChange={(value) => handleLanguageChange({ value })}
						>
							<SelectTrigger>
								<SelectValue placeholder="Select a language" />
							</SelectTrigger>
							<SelectContent>
								<SelectItem value="auto">Auto detect</SelectItem>
								{TRANSCRIPTION_LANGUAGES.map((language) => (
									<SelectItem key={language.code} value={language.code}>
										{language.name}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</SectionField>
					<label className="flex items-center gap-2 text-sm">
						<input
							type="checkbox"
							checked={translate}
							onChange={(event) => setTranslate(event.target.checked)}
						/>
						Translate transcript
					</label>
					{translate && (
						<SectionField label="Target language">
							<Select
								value={targetLanguage}
								onValueChange={setTargetLanguage}
							>
								<SelectTrigger>
									<SelectValue placeholder="Select a target language" />
								</SelectTrigger>
								<SelectContent>
									{TRANSCRIPTION_LANGUAGES.map((language) => (
										<SelectItem key={language.code} value={language.code}>
											{language.name}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</SectionField>
					)}
				</SectionFields>

				<Button
					type="button"
					className="mt-auto w-full"
					onClick={handleTranscribeTimeline}
					disabled={isProcessing}
				>
					{isProcessing && <Spinner className="mr-1" />}
					{isProcessing ? processing.step : "Transcribe timeline to captions"}
				</Button>
				{error && (
					<div className="bg-destructive/10 border-destructive/20 rounded-md border p-3">
						<p className="text-destructive text-sm">{error}</p>
					</div>
				)}
				{message && (
					<div className="rounded-md border border-emerald-500/20 bg-emerald-500/10 p-3">
						<p className="text-sm text-emerald-700">{message}</p>
					</div>
				)}
			</SectionContent>
		</Section>
	);
}

function OmniVoiceTtsTab() {
	return (
		<Section showTopBorder={false} showBottomBorder={false} className="flex-1">
			<SectionContent className="flex h-full flex-col gap-4 pt-1">
				<p className="text-sm text-muted-foreground">
					TTS uses the OmniVoice backend endpoint from Settings. This tab is split
					out from Transcript so the editor stays focused.
				</p>
				<SectionFields>
					<SectionField label="Script">
						<Textarea
							placeholder="Enter text to synthesize..."
							className="min-h-40 resize-none"
						/>
					</SectionField>
				</SectionFields>
				<div className="rounded-md border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
					TTS controls are not wired yet.
				</div>
			</SectionContent>
		</Section>
	);
}
