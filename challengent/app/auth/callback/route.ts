import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const url = request.nextUrl.clone();
  const code = url.searchParams.get("code");
  const nextRaw = url.searchParams.get("next") ?? "/";
  const next = nextRaw.startsWith("/") ? nextRaw : `/${nextRaw}`;

  if (!code) {
    const login = new URL("/auth/login", request.nextUrl.origin);
    login.searchParams.set("error", "missing_code");
    return NextResponse.redirect(login);
  }

  const redirectUrl = new URL(next, request.nextUrl.origin);
  const response = NextResponse.redirect(redirectUrl);

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!supabaseUrl || !anonKey) {
    const login = new URL("/auth/login", request.nextUrl.origin);
    login.searchParams.set("error", "server_misconfigured");
    return NextResponse.redirect(login);
  }

  const supabase = createServerClient(supabaseUrl, anonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });

  const { error } = await supabase.auth.exchangeCodeForSession(code);
  if (error) {
    const login = new URL("/auth/login", request.nextUrl.origin);
    login.searchParams.set("error", error.message);
    return NextResponse.redirect(login);
  }

  return response;
}
