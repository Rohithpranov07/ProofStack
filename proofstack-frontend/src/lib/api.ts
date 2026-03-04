import axios, { AxiosError } from "axios";
import type { JobStatusResponse, AnalysisPayload } from "@/types";
import type { DashboardResponse } from "@/types/dashboard";

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "proofstack-demo-2025";

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
  },
});

function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    return (
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message
    );
  }
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred";
}

export const createAnalysisJob = async (
  payload: AnalysisPayload
): Promise<{ job_id: string; status: string }> => {
  try {
    const { data } = await client.post("/jobs/analyze", payload);
    return data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getJobStatus = async (
  jobId: string
): Promise<JobStatusResponse> => {
  try {
    const { data } = await client.get(`/jobs/${jobId}`);
    return data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getDashboard = async (
  jobId: string
): Promise<DashboardResponse> => {
  try {
    const { data } = await client.get(`/api/dashboard/${jobId}`);
    return data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getDashboardPdfUrl = (jobId: string): string => {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base}/api/dashboard/${jobId}/pdf?api_key=${encodeURIComponent(API_KEY)}`;
};

export const createShareLink = async (
  jobId: string
): Promise<{ token: string; share_url: string; expires_at: string | null }> => {
  try {
    const { data } = await client.post(`/api/dashboard/${jobId}/share`);
    return data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};

export const getSharedDashboard = async (
  token: string
): Promise<DashboardResponse> => {
  try {
    const { data } = await client.get(`/api/dashboard/shared/${token}`);
    return data;
  } catch (error) {
    throw new Error(extractErrorMessage(error));
  }
};
