# OpenPango Mobile HITL Companion

Lightweight React Native (Expo) companion app for Human-In-The-Loop approvals.

## Features
- Connects to OpenPango node API (configurable URL)
- Lists pending `Approval Required` actions
- Shows action payload, risk, cost, and optional diff
- Approve/Reject buttons
- Push notification registration scaffold via Expo Notifications

## Configure node URL
Set environment variable before running:

```bash
EXPO_PUBLIC_OPENPANGO_NODE_URL=http://localhost:3030
```

Expected API endpoints:
- `GET /api/hitl/pending`
- `POST /api/hitl/:id/approve`
- `POST /api/hitl/:id/reject`

## Run
```bash
cd mobile/hitl-companion
npm install
npm run start
```

## Security notes
- Use HTTPS and token-auth for remote nodes.
- Node should verify that approve/reject actions are user-authorized.
- Push token registration should be bound to an authenticated user/session.
