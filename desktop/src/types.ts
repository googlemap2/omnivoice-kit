export type BackendHealth = {
  ok?: boolean;
  status?: string;
  service?: string;
  version?: string;
  [key: string]: unknown;
};

export type ConnectionResult = {
  ok: boolean;
  status: number;
  message: string;
  data?: BackendHealth;
};
