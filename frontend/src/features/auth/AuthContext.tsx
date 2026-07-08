import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { getCurrentUser, login as loginRequest, register as registerRequest } from "../../api/auth";
import { clearToken, getStoredToken, storeToken } from "../../api/client";
import type { User } from "../../types/domain";
import { AuthContext } from "./auth-context";
import type { AuthContextValue } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  useEffect(() => {
    let isMounted = true;
    async function loadUser() {
      if (!token) {
        setUser(null);
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await getCurrentUser();
        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        clearToken();
        if (isMounted) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    void loadUser();
    return () => {
      isMounted = false;
    };
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(token && user),
      async login(email: string, password: string) {
        const response = await loginRequest({ email, password });
        storeToken(response.access_token);
        setToken(response.access_token);
        setUser(await getCurrentUser());
      },
      async register(fullName: string, email: string, password: string) {
        await registerRequest({ full_name: fullName, email, password });
        const response = await loginRequest({ email, password });
        storeToken(response.access_token);
        setToken(response.access_token);
        setUser(await getCurrentUser());
      },
      logout() {
        clearToken();
        setToken(null);
        setUser(null);
      },
    }),
    [isLoading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
