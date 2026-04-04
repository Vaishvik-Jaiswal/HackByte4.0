/** Mirrors FastAPI ``AskResponseOut`` / ``ThreadDetailOut`` (subset for UI). */

export type AnswerBlock = {
  answer: string;
  supporting_email: string;
  summary: string;
  confidence: number;
};

export type RetrievalThread = {
  thread_id: string;
  best_similarity: number;
  hit_count: number;
};

export type AskResponse = {
  query: string;
  thread_id: string;
  retrieval: {
    best_similarity: number;
    hit_count: number;
    threads: RetrievalThread[];
  };
  answer: AnswerBlock;
};

export type ThreadEmail = {
  id: number;
  thread_id: string;
  gmail_msg_id: string;
  from_json: unknown;
  to_json: unknown;
  subject: string;
  body_text: string;
  date: string;
  sender_display: string;
};

export type ThreadDetail = {
  thread_id: string;
  emails: ThreadEmail[];
};
