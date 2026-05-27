import { Typography } from "@mui/material";

export function SectionTitle({ title }: { title: string }) {
  return (
    <Typography sx={{ px: 2, py: 0.75, fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>
      {title}
    </Typography>
  );
}
