/**
 * CategoryView component - displays categorized emails.
 */
import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { EmailCard } from './EmailCard';
import { Briefcase, Heart, Tag, AlertCircle } from 'lucide-react';

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
}

interface CategoryViewProps {
  categories: {
    Work: Email[];
    Personal: Email[];
    Promotions: Email[];
    Urgent: Email[];
  };
  digest?: string;
  onGenerateReply: (email: Email) => Promise<string>;
  onSendReply: (email: Email, replyText: string) => Promise<void>;
  onDelete: (email: Email) => Promise<void>;
}

const categoryIcons = {
  Work: Briefcase,
  Personal: Heart,
  Promotions: Tag,
  Urgent: AlertCircle,
};

const categoryColors = {
  Work: 'border-blue-500',
  Personal: 'border-green-500',
  Promotions: 'border-purple-500',
  Urgent: 'border-red-500',
};

export function CategoryView({
  categories,
  digest,
  onGenerateReply,
  onSendReply,
  onDelete,
}: CategoryViewProps) {
  return (
    <div className="space-y-6">
      {/* Daily Digest */}
      {digest && (
        <Card className="border-2 border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Daily Digest
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="whitespace-pre-wrap">{digest}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Categorized Emails */}
      {Object.entries(categories).map(([category, emails]) => {
        if (emails.length === 0) return null;

        const Icon = categoryIcons[category as keyof typeof categoryIcons];
        const colorClass = categoryColors[category as keyof typeof categoryColors];

        return (
          <Card key={category} className={`border-l-4 ${colorClass}`}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Icon className="h-5 w-5" />
                {category}
                <span className="text-sm text-muted-foreground font-normal">
                  ({emails.length})
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {emails.map((email) => (
                <EmailCard
                  key={email.id}
                  email={email}
                  onGenerateReply={onGenerateReply}
                  onSendReply={onSendReply}
                  onDelete={onDelete}
                />
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
