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
  const apiBaseUrl = NEXT_PUBLIC_API_BASE_URL || "";
  const maskedApiBaseUrl = maskApiUrl(apiBaseUrl);

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
      <Chip size="small" label={`FastAPI ${maskedApiBaseUrl || "not configured"}`} sx={{ height: 22 }} />
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

function maskApiUrl(value: string) {
  if (!value) return "";
  try {
    const url = new URL(value);
    const hostname = url.hostname;
    const maskLength = Math.max(3, Math.ceil(hostname.length / 3));
    const startLength = Math.max(1, Math.floor((hostname.length - maskLength) / 2));
    const endLength = Math.max(1, hostname.length - maskLength - startLength);
    const maskedHost =
      hostname.length <= 8
        ? `${hostname.slice(0, 2)}***${hostname.slice(-2)}`
        : `${hostname.slice(0, startLength)}***${hostname.slice(-endLength)}`;
    return `${url.protocol}//${maskedHost}${url.port ? `:${url.port}` : ""}${url.pathname === "/" ? "" : url.pathname}`;
  } catch {
    const maskLength = Math.max(3, Math.ceil(value.length / 3));
    const startLength = Math.max(1, Math.floor((value.length - maskLength) / 2));
    const endLength = Math.max(1, value.length - maskLength - startLength);
    return `${value.slice(0, startLength)}***${value.slice(-endLength)}`;
  }
}
