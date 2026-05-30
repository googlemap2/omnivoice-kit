import HistoryIcon from "@mui/icons-material/History";
import { Alert, Box, Tab, Tabs, Typography } from "@mui/material";
import type { HistoryEntry } from "../../types/api";

type BottomPanelProps = {
  error: string | null;
  message: string;
  history: HistoryEntry[];
};

export function BottomPanel({ error, message, history }: BottomPanelProps) {
  return (
    <Box sx={{ borderTop: "1px solid", borderColor: "divider", bgcolor: "#1b1b1b", minHeight: 0 }}>
      <Tabs value="output" sx={{ minHeight: 32, "& .MuiTab-root": { minHeight: 32, py: 0 } }}>
        <Tab value="output" icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="Output" />
      </Tabs>
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
          gap: 2,
          px: 2,
          pb: 1,
          height: { xs: 220, md: 132 },
        }}
      >
        <Box sx={{ overflow: "auto" }}>
          {error ? <Alert severity="error">{error}</Alert> : <Alert severity="info">{message}</Alert>}
        </Box>
        <Box sx={{ overflow: "auto" }}>
          {history.slice(0, 8).map((item) => (
            <Typography
              key={item.id}
              sx={{ fontSize: 12, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}
            >
              {item.created_at} - {item.mode} - {item.voice || "no voice"} - {item.text}
            </Typography>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
