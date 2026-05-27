import type { ReactNode } from "react";
import { StudioFrame } from "../../features/studio/StudioFrame";
import { StudioProvider } from "../../features/studio/StudioContext";

export default function StudioLayout({ children }: { children: ReactNode }) {
  return (
    <StudioProvider>
      <StudioFrame>{children}</StudioFrame>
    </StudioProvider>
  );
}
