'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Mail, Bot, Sparkles, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

export default function Home() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check for error parameter
    const error = searchParams.get('error');
    if (error) {
      let message = 'Authentication failed';
      if (error === 'access_denied') {
        message = 'Access was denied. Please try again.';
      } else if (error === 'no_code') {
        message = 'No authorization code received.';
      } else if (error === 'auth_failed') {
        message = 'Authentication failed. Please try again.';
      }

      toast({
        title: 'Authentication Error',
        description: message,
        variant: 'destructive',
      });
    }

    // Check if already authenticated
    const token = localStorage.getItem('auth_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [searchParams, router, toast]);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      const authUrl = await apiClient.getAuthUrl();
      window.location.href = authUrl;
    } catch (error) {
      console.error('Login error:', error);
      toast({
        title: 'Error',
        description: 'Failed to initiate login. Please try again.',
        variant: 'destructive',
      });
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Title */}
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-primary rounded-2xl p-4">
              <Mail className="h-12 w-12 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            AI Email Assistant
          </h1>
          <p className="text-muted-foreground text-lg">
            Intelligent email management powered by AI
          </p>
        </div>

        {/* Login Card */}
        <Card className="shadow-xl">
          <CardHeader className="text-center">
            <CardTitle>Welcome</CardTitle>
            <CardDescription>
              Sign in with your Google account to get started
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={handleLogin}
              disabled={isLoading}
              className="w-full h-12 text-base"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Mail className="mr-2 h-5 w-5" />
                  Sign in with Google
                </>
              )}
            </Button>

            {/* Features */}
            <div className="pt-4 space-y-3">
              <div className="flex items-start gap-3">
                <Bot className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">AI-Powered Summaries</p>
                  <p className="text-xs text-muted-foreground">
                    Get instant summaries of your emails
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Smart Replies</p>
                  <p className="text-xs text-muted-foreground">
                    Generate context-aware responses automatically
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Mail className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Intelligent Organization</p>
                  <p className="text-xs text-muted-foreground">
                    Categorize and manage emails effortlessly
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          By signing in, you agree to grant access to read, send, and manage
          your Gmail messages.
        </p>
      </div>
    </div>
  );
}
