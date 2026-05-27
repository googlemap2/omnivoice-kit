import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";

type SelectFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ id: string; label: string }>;
};

export function SelectField({ label, value, onChange, options }: SelectFieldProps) {
  return (
    <FormControl size="small" fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select label={label} value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <MenuItem key={option.id} value={option.id}>
            {option.label || option.id}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
