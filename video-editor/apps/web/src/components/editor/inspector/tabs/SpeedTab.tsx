import React from "react";
import type { Clip } from "@openreel/core";
import { SpeedSection, StabilizationSection, SpeedRampSection } from "../";
import { InspectorSection } from "../shell/InspectorSection";

interface SpeedTabClip {
  id: string;
  mediaId: string;
}

export interface SpeedTabProps {
  clipType: string | null;
  showVideoControls: boolean;
  selectedClip: SpeedTabClip | null;
}

export const SpeedTab: React.FC<SpeedTabProps> = ({
  clipType,
  showVideoControls,
  selectedClip,
}) => {
  const isMediaClip =
    selectedClip &&
    !selectedClip.mediaId.startsWith("text-") &&
    !selectedClip.mediaId.startsWith("shape-") &&
    !selectedClip.mediaId.startsWith("svg-") &&
    !selectedClip.mediaId.startsWith("sticker-");
  const showSpeedControls =
    isMediaClip &&
    (showVideoControls || clipType === "audio");

  return (
    <>
      {showSpeedControls && selectedClip && (
          <>
            <InspectorSection
              title="Speed & Direction"
              sectionId="speed"
              defaultOpen={true}
            >
              <SpeedSection clip={selectedClip as Clip} />
            </InspectorSection>
          </>
        )}
      {showVideoControls &&
        isMediaClip &&
        selectedClip && (
          <InspectorSection
            title="Stabilization"
            sectionId="stabilization"
            defaultOpen={false}
          >
            <StabilizationSection clip={selectedClip as Clip} />
          </InspectorSection>
        )}
      {showVideoControls &&
        isMediaClip &&
        selectedClip && (
          <InspectorSection
            title="Speed Curves"
            sectionId="speed-curves"
            defaultOpen={false}
          >
            <SpeedRampSection clip={selectedClip as Clip} />
          </InspectorSection>
        )}
    </>
  );
};
