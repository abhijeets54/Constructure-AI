/**
 * ChatMessage component - displays a single message in the chat interface.
 */
import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
  userInfo?: {
    name: string;
    picture?: string;
  };
}

export function ChatMessage({ message, userInfo }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 flex-shrink-0">
        {isUser ? (
          userInfo?.picture ? (
            <AvatarImage src={userInfo.picture} alt={userInfo.name} />
          ) : (
            <AvatarFallback className="bg-primary text-primary-foreground">
              <User className="h-4 w-4" />
            </AvatarFallback>
          )
        ) : (
          <AvatarFallback className="bg-secondary">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        )}
      </Avatar>

      {/* Message bubble */}
      <div
        className={cn(
          'rounded-lg px-4 py-2 max-w-[80%]',
          isUser
            ? 'bg-primary text-primary-foreground'
            : isSystem
            ? 'bg-muted text-muted-foreground border'
            : 'bg-secondary text-secondary-foreground'
        )}
      >
        <p className="text-sm whitespace-pre-wrap break-words">
          {message.content}
        </p>
        <p
          className={cn(
            'text-xs mt-1 opacity-70',
            isUser ? 'text-right' : 'text-left'
          )}
        >
          {message.timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
