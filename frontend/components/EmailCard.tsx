/**
 * EmailCard component - displays an email with AI summary and action buttons.
 * Includes beautiful popup dialogs for Reply and Delete confirmations.
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Mail, Trash2, Reply, Loader2, Send, AlertTriangle, Sparkles } from 'lucide-react';

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
  ai_reply?: string;
  thread_id?: string;
}

interface EmailCardProps {
  email: Email;
  onGenerateReply: (email: Email) => Promise<string>;
  onSendReply: (email: Email, replyText: string) => Promise<void>;
  onDelete: (email: Email) => Promise<void>;
}

export function EmailCard({ email, onGenerateReply, onSendReply, onDelete }: EmailCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showReplyDialog, setShowReplyDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  const handleReplyClick = async () => {
    setShowReplyDialog(true);
    setIsGeneratingReply(true);
    setReplyText('');

    try {
      // Generate AI reply
      const generatedReply = await onGenerateReply(email);
      setReplyText(generatedReply);
    } catch (error) {
      console.error('Error generating reply:', error);
      setReplyText('');
    } finally {
      setIsGeneratingReply(false);
    }
  };

  const handleConfirmReply = async () => {
    if (!replyText.trim()) return;

    setIsSending(true);
    try {
      await onSendReply(email, replyText);
      setShowReplyDialog(false);
      setReplyText('');
    } catch (error) {
      console.error('Error sending reply:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete(email);
      setShowDeleteDialog(false);
    } catch (error) {
      console.error('Error deleting:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Card className="mb-4 hover:shadow-md transition-shadow border-l-4 border-l-primary/20 hover:border-l-primary">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <Avatar className="h-10 w-10 ring-2 ring-primary/10">
                <AvatarFallback className="bg-gradient-to-br from-primary to-primary/70 text-primary-foreground font-semibold">
                  {getInitials(email.sender_name || email.sender_email)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-sm truncate">
                    {email.sender_name || email.sender_email}
                  </h3>
                  <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                    {formatDate(email.date)}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground truncate">
                  {email.sender_email}
                </p>
              </div>
            </div>
            <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          <h4 className="font-medium text-base mb-2">{email.subject}</h4>

          {/* AI Summary */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/50 border border-blue-200 dark:border-blue-800 rounded-lg p-3 mb-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Sparkles className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
              <p className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                AI Summary
              </p>
            </div>
            <p className="text-sm text-blue-900 dark:text-blue-100">
              {email.ai_summary}
            </p>
          </div>

          {/* Snippet or full body */}
          <div className="text-sm text-muted-foreground overflow-hidden">
            <p className={`break-words whitespace-pre-wrap overflow-wrap-anywhere ${isExpanded ? 'max-h-96 overflow-y-auto' : 'line-clamp-2'}`}>
              {email.body || email.snippet}
            </p>
            {!isExpanded && email.body && email.body.length > 150 && (
              <button
                onClick={() => setIsExpanded(true)}
                className="text-primary hover:underline text-xs mt-1 font-medium"
              >
                Show more
              </button>
            )}
            {isExpanded && (
              <button
                onClick={() => setIsExpanded(false)}
                className="text-primary hover:underline text-xs mt-1 font-medium"
              >
                Show less
              </button>
            )}
          </div>
        </CardContent>

        <CardFooter className="pt-0 gap-2">
          <Button
            size="sm"
            variant="default"
            onClick={handleReplyClick}
            className="flex-1 bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70"
          >
            <Reply className="h-4 w-4 mr-2" />
            Reply
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
            className="flex-1"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </CardFooter>
      </Card>

      {/* Reply Dialog */}
      <Dialog open={showReplyDialog} onOpenChange={setShowReplyDialog}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Reply className="h-5 w-5 text-primary" />
              Reply to {email.sender_name || email.sender_email}
            </DialogTitle>
            <DialogDescription>
              Replying to: <span className="font-medium">{email.subject}</span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* AI Suggested Reply Badge */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/30 dark:to-blue-950/30 p-2 rounded-md border border-purple-200 dark:border-purple-800">
              <Sparkles className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
              <span>AI-generated reply. Feel free to customize it!</span>
            </div>

            {isGeneratingReply ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary mr-2" />
                <span className="text-muted-foreground">Generating smart reply...</span>
              </div>
            ) : (
              <Textarea
                placeholder="Type your reply here..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="min-h-[150px] resize-none"
              />
            )}
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowReplyDialog(false)}
              disabled={isSending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleConfirmReply}
              disabled={isSending || isGeneratingReply || !replyText.trim()}
              className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
            >
              {isSending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send Reply
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Confirm Deletion
            </DialogTitle>
            <DialogDescription className="pt-2">
              Are you sure you want to delete this email?
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <div className="bg-muted/50 rounded-lg p-4 space-y-2">
              <p className="text-sm">
                <span className="font-medium">From:</span> {email.sender_name || email.sender_email}
              </p>
              <p className="text-sm">
                <span className="font-medium">Subject:</span> {email.subject}
              </p>
            </div>
            <p className="text-xs text-muted-foreground mt-3 text-center">
              This action cannot be undone. The email will be permanently deleted.
            </p>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={isDeleting}
            >
              No, Keep It
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Yes, Delete
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
