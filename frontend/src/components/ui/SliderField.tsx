import { Box, Slider, Stack, Typography } from "@mui/material";

type SliderFieldProps = {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
};

export function SliderField({ label, value, min, max, step, onChange }: SliderFieldProps) {
  return (
    <Box>
      <Stack direction="row" justifyContent="space-between">
        <Typography sx={{ fontSize: 12 }}>{label}</Typography>
        <Typography sx={{ fontSize: 12, color: "text.secondary" }}>{value}</Typography>
      </Stack>
      <Slider
        size="small"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(_, next) => onChange(Number(next))}
      />
    </Box>
  );
}
