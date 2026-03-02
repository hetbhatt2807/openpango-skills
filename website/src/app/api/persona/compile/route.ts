import { NextResponse } from "next/server";
import {
  compilePersonaPayload,
  generateSoulMarkdown,
  personaToYaml,
  toPersonaDocument,
} from "@/lib/persona";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const persona = compilePersonaPayload(body);
    const document = toPersonaDocument(persona);

    return NextResponse.json({
      ok: true,
      persona: document,
      soulMarkdown: generateSoulMarkdown(persona),
      yaml: personaToYaml(document),
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "invalid payload";
    return NextResponse.json({ ok: false, error: message }, { status: 400 });
  }
}
