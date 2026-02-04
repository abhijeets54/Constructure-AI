/**
 * API client for backend communication.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }

  public setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  private clearToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // Auth endpoints
  async getAuthUrl(): Promise<string> {
    const response = await this.client.get('/auth/login');
    return response.data.authorization_url;
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async logout() {
    await this.client.post('/auth/logout');
    this.clearToken();
  }

  // Email endpoints
  async getEmails(limit: number = 5) {
    const response = await this.client.get('/emails', {
      params: { limit },
    });
    return response.data;
  }

  async generateReply(emailId: string, customContext?: string) {
    const response = await this.client.post('/emails/reply/generate', {
      email_id: emailId,
      custom_context: customContext,
    });
    return response.data;
  }

  async sendEmail(to: string, subject: string, body: string, threadId?: string) {
    const response = await this.client.post('/emails/send', {
      to,
      subject,
      body,
      thread_id: threadId,
    });
    return response.data;
  }

  async deleteEmail(emailId: string) {
    const response = await this.client.post('/emails/delete', {
      email_id: emailId,
    });
    return response.data;
  }

  // Chat endpoints
  async sendChatMessage(message: string, conversationHistory: any[] = []) {
    const response = await this.client.post('/chat', {
      message,
      conversation_history: conversationHistory,
    });
    return response.data;
  }

  async categorizeEmails(limit: number = 20) {
    const response = await this.client.post('/chat/categorize', null, {
      params: { limit },
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
