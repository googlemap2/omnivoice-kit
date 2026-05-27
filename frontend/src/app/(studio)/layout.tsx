import type { ReactNode } from "react";
import { StudioFrame } from "../../components/studio/StudioFrame";
import { StudioProvider } from "../../components/studio/StudioContext";

export default function StudioLayout({ children }: { children: ReactNode }) {
  return (
    <StudioProvider>
      <StudioFrame>{children}</StudioFrame>
    </StudioProvider>
  );
}
