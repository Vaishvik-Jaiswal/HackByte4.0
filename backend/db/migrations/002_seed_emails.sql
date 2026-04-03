-- Inbox Copilot — Phase 1: seed data
-- 3 threads; NVIDIA scheduling scenario includes reschedule + final confirmation.
-- To re-run after a previous seed: TRUNCATE emails RESTART IDENTITY CASCADE;

BEGIN;

INSERT INTO emails (thread_id, gmail_msg_id, from_json, to_json, subject, body_text, date) VALUES
-- ========== Thread 1: NVIDIA assessment scheduling (5 emails) ==========
(
  'thread-nvidia-onsite-2025',
  '<nvidia.001.recruiter@mail.gmail.com>',
  '{"name": "Priya Sharma", "email": "priya.sharma@nvidia.com"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'NVIDIA — Technical assessment scheduling',
  E'Hi Alex,\n\nThank you for your interest in the Software Intern role. We would like to schedule your online technical assessment.\n\nPlease reply with 2–3 time windows (PT) that work for you next week.\n\nBest,\nPriya\nNVIDIA University Recruiting',
  '2025-03-10T18:00:00Z'
),
(
  'thread-nvidia-onsite-2025',
  '<nvidia.002.candidate@mail.gmail.com>',
  '{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}'::jsonb,
  '[{"name": "Priya Sharma", "email": "priya.sharma@nvidia.com"}]'::jsonb,
  'Re: NVIDIA — Technical assessment scheduling',
  E'Hi Priya,\n\nThanks for reaching out. I am available:\n- Tue Mar 18, 9am–12pm PT\n- Wed Mar 19, 1pm–5pm PT\n- Thu Mar 20, 10am–2pm PT\n\nLet me know what works on your side.\n\nBest,\nAlex',
  '2025-03-11T02:15:00Z'
),
(
  'thread-nvidia-onsite-2025',
  '<nvidia.003.recruiter@mail.gmail.com>',
  '{"name": "Priya Sharma", "email": "priya.sharma@nvidia.com"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'NVIDIA test scheduling — proposed slot',
  E'Hi Alex,\n\nGreat — we can hold NVIDIA test scheduling for Thursday Mar 20, 11:00 AM PT. You will receive a calendar invite and the assessment link 24 hours before.\n\nPlease confirm by EOD tomorrow.\n\nThanks,\nPriya',
  '2025-03-12T16:30:00Z'
),
(
  'thread-nvidia-onsite-2025',
  '<nvidia.004.recruiter@mail.gmail.com>',
  '{"name": "Priya Sharma", "email": "priya.sharma@nvidia.com"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'Reschedule: NVIDIA technical assessment',
  E'Hi Alex,\n\nWe need to reschedule your NVIDIA technical assessment due to an internal calibration window. Sorry for the inconvenience.\n\nNew proposed times (PT):\n- Mon Mar 24, 9:00 AM\n- Tue Mar 25, 2:00 PM\n\nReply with your preference and we will lock it in.\n\nPriya',
  '2025-03-14T19:00:00Z'
),
(
  'thread-nvidia-onsite-2025',
  '<nvidia.005.recruiter@mail.gmail.com>',
  '{"name": "Priya Sharma", "email": "priya.sharma@nvidia.com"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'Final confirmation — NVIDIA assessment Tue Mar 25',
  E'Hi Alex,\n\nThis is the final confirmation email: your NVIDIA assessment is confirmed for Tuesday, March 25, 2025 at 2:00 PM PT.\n\nLink: (placeholder) — active 15 minutes before start.\n\nGood luck,\nPriya',
  '2025-03-17T17:00:00Z'
),

-- ========== Thread 2: Hackathon team logistics (4 emails) ==========
(
  'thread-hackbyte-logistics',
  '<hackbyte.001.lead@mail.gmail.com>',
  '{"name": "Sam Rivera", "email": "sam@hackbyte.dev"}'::jsonb,
  '[{"name": "Jamie Lee", "email": "jamie@student.org"}]'::jsonb,
  'HackByte — repo access + judging format',
  E'Jamie,\n\nWelcome to the team. I have added you to the org repo. Judging is demo-first; keep slides under 3 minutes.\n\nSam',
  '2025-03-08T14:00:00Z'
),
(
  'thread-hackbyte-logistics',
  '<hackbyte.002.jamie@mail.gmail.com>',
  '{"name": "Jamie Lee", "email": "jamie@student.org"}'::jsonb,
  '[{"name": "Sam Rivera", "email": "sam@hackbyte.dev"}]'::jsonb,
  'Re: HackByte — repo access + judging format',
  E'Sam — confirmed, I see the invite. For the demo, we will lead with the live inbox query and keep backup slides offline.\n\nJamie',
  '2025-03-08T22:40:00Z'
),
(
  'thread-hackbyte-logistics',
  '<hackbyte.003.lead@mail.gmail.com>',
  '{"name": "Sam Rivera", "email": "sam@hackbyte.dev"}'::jsonb,
  '[{"name": "Jamie Lee", "email": "jamie@student.org"}]'::jsonb,
  'Re: HackByte — repo access + judging format',
  E'Perfect. I will book a dry run Sunday 6pm. Calendar invite incoming.\n\nSam',
  '2025-03-09T15:10:00Z'
),
(
  'thread-hackbyte-logistics',
  '<hackbyte.004.jamie@mail.gmail.com>',
  '{"name": "Jamie Lee", "email": "jamie@student.org"}'::jsonb,
  '[{"name": "Sam Rivera", "email": "sam@hackbyte.dev"}]'::jsonb,
  'Re: HackByte — repo access + judging format',
  E'Invite received. See you Sunday.\n\nJamie',
  '2025-03-09T15:25:00Z'
),

-- ========== Thread 3: Career fair follow-up (3 emails) ==========
(
  'thread-career-fair-followup',
  '<career.001.corp@mail.gmail.com>',
  '{"name": "Morgan Blake", "email": "morgan.blake@bigcorp.io"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'Great meeting you at the career fair',
  E'Hi Alex,\n\nIt was great to chat at the booth. If you are still interested in our new grad roles, here is the application link: https://example.com/apply\n\nMorgan',
  '2025-03-05T21:00:00Z'
),
(
  'thread-career-fair-followup',
  '<career.002.student@mail.gmail.com>',
  '{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}'::jsonb,
  '[{"name": "Morgan Blake", "email": "morgan.blake@bigcorp.io"}]'::jsonb,
  'Re: Great meeting you at the career fair',
  E'Hi Morgan,\n\nThanks — I submitted my application yesterday. Happy to share my portfolio if helpful.\n\nAlex',
  '2025-03-06T03:30:00Z'
),
(
  'thread-career-fair-followup',
  '<career.003.corp@mail.gmail.com>',
  '{"name": "Morgan Blake", "email": "morgan.blake@bigcorp.io"}'::jsonb,
  '[{"name": "Alex Chen", "email": "alex.chen.student@university.edu"}]'::jsonb,
  'Re: Great meeting you at the career fair',
  E'Alex — received. Our university team will review and follow up within two weeks.\n\nMorgan',
  '2025-03-07T18:45:00Z'
);

COMMIT;
