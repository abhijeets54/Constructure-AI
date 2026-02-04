'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { ChatMessage, Message } from '@/components/ChatMessage';
import { EmailCard } from '@/components/EmailCard';
import { CategoryView } from '@/components/CategoryView';
import { useToast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api';
import {
  Send,
  Loader2,
  LogOut,
  Mail,
  User,
  Sparkles,
  AlertCircle,
} from 'lucide-react';

interface UserInfo {
  email: string;
  name: string;
  picture?: string;
}

interface Email {
  id: string;
  subject: string;
  sender_name: string;
  sender_email: string;
  from: string;
  date: string;
  snippet: string;
  ai_summary: string;
  body?: string;
  thread_id?: string;
}

export default function Dashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [emails, setEmails] = useState<Email[]>([]);
  const [categories, setCategories] = useState<any>(null);
  const [digest, setDigest] = useState<string>('');

  useEffect(() => {
    initializeDashboard();
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const initializeDashboard = async () => {
    try {
      // Check for token in URL (from OAuth callback)
      const token = searchParams.get('token');
      if (token) {
        apiClient.setToken(token);
        // Clean up URL
        window.history.replaceState({}, '', '/dashboard');
      }

      // Verify authentication
      const userData = await apiClient.getCurrentUser();
      setUserInfo(userData.user);

      // Add welcome message
      addMessage('system', `Welcome back, ${userData.user.name}! 👋

I'm your AI email assistant. Here's what I can help you with:

• **Read Emails**: Say "Show me my latest emails" or "What's in my inbox?"
• **Daily Digest**: Ask for "daily digest" or "categorize my emails"
• **Reply to Emails**: Click the Reply button on any email to generate a smart response
• **Delete Emails**: Click the Delete button to remove unwanted messages

Just type your request naturally, and I'll take care of it!`);

      setIsInitializing(false);
    } catch (error) {
      console.error('Initialization error:', error);
      toast({
        title: 'Authentication Error',
        description: 'Please log in again.',
        variant: 'destructive',
      });
      router.push('/');
    }
  };

  const addMessage = (role: 'user' | 'assistant' | 'system', content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    addMessage('user', userMessage);
    setIsLoading(true);

    try {
      const response = await apiClient.sendChatMessage(userMessage);

      // Handle different response types
      if (response.emails) {
        setEmails(response.emails);
        setCategories(null);
        setDigest('');
        addMessage('assistant', response.message || 'Here are your emails:');
      } else if (response.categories) {
        setCategories(response.categories);
        setDigest(response.digest || '');
        setEmails([]);
        addMessage('assistant', response.message || "Here's your categorized email overview:");
      } else {
        addMessage('assistant', response.message || 'I processed your request.');
      }
    } catch (error: any) {
      console.error('Chat error:', error);
      addMessage(
        'system',
        `Error: ${error.response?.data?.detail || 'Failed to process your request. Please try again.'}`
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReply = async (email: Email): Promise<string> => {
    try {
      const response = await apiClient.generateReply(email.id);
      return response.reply;
    } catch (error: any) {
      console.error('Reply generation error:', error);
      toast({
        title: 'Error',
        description: 'Failed to generate reply. Please try again.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const handleSendReply = async (email: Email, replyText: string): Promise<void> => {
    try {
      await apiClient.sendEmail(
        email.sender_email,
        `Re: ${email.subject}`,
        replyText,
        email.thread_id
      );

      addMessage('assistant', `✅ Reply sent to ${email.sender_name || email.sender_email}!`);

      toast({
        title: 'Success',
        description: 'Email sent successfully!',
      });
    } catch (error: any) {
      console.error('Send error:', error);
      addMessage('system', 'Failed to send email. Please try again.');
      toast({
        title: 'Error',
        description: 'Failed to send email.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const handleDelete = async (email: Email): Promise<void> => {
    try {
      await apiClient.deleteEmail(email.id);

      // Remove from state
      setEmails((prev) => prev.filter((e) => e.id !== email.id));

      if (categories) {
        const updatedCategories = { ...categories };
        Object.keys(updatedCategories).forEach((category) => {
          updatedCategories[category] = updatedCategories[category].filter(
            (e: Email) => e.id !== email.id
          );
        });
        setCategories(updatedCategories);
      }

      addMessage('assistant', `✅ Email "${email.subject}" deleted successfully!`);

      toast({
        title: 'Success',
        description: 'Email deleted successfully!',
      });
    } catch (error: any) {
      console.error('Delete error:', error);
      addMessage('system', 'Failed to delete email. Please try again.');
      toast({
        title: 'Error',
        description: 'Failed to delete email.',
        variant: 'destructive',
      });
      throw error;
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      router.push('/');
    } catch (error) {
      console.error('Logout error:', error);
      router.push('/');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b shadow-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary rounded-lg p-2">
              <Mail className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold">AI Email Assistant</h1>
              <p className="text-xs text-muted-foreground">
                {userInfo?.email}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Avatar>
              {userInfo?.picture ? (
                <AvatarImage src={userInfo.picture} alt={userInfo.name} />
              ) : (
                <AvatarFallback>
                  <User className="h-5 w-5" />
                </AvatarFallback>
              )}
            </Avatar>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 max-w-5xl">
        <div className="grid grid-cols-1 gap-6">
          {/* Chat Area */}
          <Card className="shadow-xl border-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
            <CardContent className="p-0">
              {/* Messages */}
              <div className="h-[450px] overflow-y-auto p-4 scroll-smooth">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    userInfo={userInfo || undefined}
                  />
                ))}
                {isLoading && (
                  <div className="flex items-center gap-2 text-muted-foreground p-3 bg-muted/30 rounded-lg animate-pulse">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">AI is thinking...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t bg-muted/20 p-4">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder='Ask me anything... (e.g., "Show me my emails", "Daily digest")'
                    className="flex-1 px-4 py-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary bg-white dark:bg-gray-800 shadow-sm transition-all"
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={isLoading || !inputMessage.trim()}
                    className="px-6 rounded-xl shadow-md hover:shadow-lg transition-all bg-gradient-to-r from-primary to-primary/80"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Email Display Area */}
          {categories ? (
            <CategoryView
              categories={categories}
              digest={digest}
              onGenerateReply={handleGenerateReply}
              onSendReply={handleSendReply}
              onDelete={handleDelete}
            />
          ) : emails.length > 0 ? (
            <div className="space-y-3">
              {emails.map((email) => (
                <EmailCard
                  key={email.id}
                  email={email}
                  onGenerateReply={handleGenerateReply}
                  onSendReply={handleSendReply}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
}
