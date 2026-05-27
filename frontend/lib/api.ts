import axios, { AxiosInstance } from "axios";
import { getSession } from "next-auth/react";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({ baseURL: BASE_URL, timeout: 10_000 });

    this.client.interceptors.request.use(async (config) => {
      const session = await getSession();
      if (session?.accessToken) {
        config.headers.Authorization = `Bearer ${session.accessToken}`;
      }
      return config;
    });
  }

  async get<T>(url: string): Promise<T> {
    const res = await this.client.get<T>(url);
    return res.data;
  }

  async post<T>(url: string, data: unknown): Promise<T> {
    const res = await this.client.post<T>(url, data);
    return res.data;
  }

  async put<T>(url: string, data: unknown): Promise<T> {
    const res = await this.client.put<T>(url, data);
    return res.data;
  }

  async delete<T>(url: string): Promise<T> {
    const res = await this.client.delete<T>(url);
    return res.data;
  }
}

export const apiClient = new ApiClient();
