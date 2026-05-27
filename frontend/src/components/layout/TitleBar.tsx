import RefreshIcon from "@mui/icons-material/Refresh";
import {
  Box,
  Chip,
  IconButton,
  LinearProgress,
  Tooltip,
  Typography,
} from "@mui/material";
import { NEXT_PUBLIC_API_BASE_URL } from "../../constant/constant";

type TitleBarProps = {
  busy: boolean;
  onRefresh: () => void;
};

export function TitleBar({ busy, onRefresh }: TitleBarProps) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        px: 1,
        borderBottom: "1px solid",
        borderColor: "divider",
        bgcolor: "#2d2d30",
      }}>
      <Typography sx={{ fontSize: 13, fontWeight: 600, mr: 2 }}>
        OmniVoice Studio
      </Typography>
      <Chip
        size="small"
        label={`FastAPI ${NEXT_PUBLIC_API_BASE_URL}`}
        sx={{ height: 22 }}
      />
      <Box sx={{ flex: 1 }} />
      {busy && <LinearProgress sx={{ width: 160, mr: 1 }} />}
      <Tooltip title="Refresh workspace data">
        <IconButton size="small" onClick={onRefresh}>
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
