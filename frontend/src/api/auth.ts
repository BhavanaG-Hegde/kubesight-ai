import { apiRequest } from "./client";
import type { TokenResponse, User } from "../types/domain";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload extends LoginPayload {
  full_name: string;
}

export function login(payload: LoginPayload): Promise<TokenResponse> {
  return apiRequest<TokenResponse>(
    "/api/v1/auth/login",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    false,
  );
}

export function register(payload: RegisterPayload): Promise<User> {
  return apiRequest<User>(
    "/api/v1/auth/register",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    false,
  );
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/api/v1/auth/me");
}
