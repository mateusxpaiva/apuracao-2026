-- Apuração por IA · banco no Supabase
-- Cole tudo no Supabase: SQL Editor > New query > Run. Pode rodar de novo sem quebrar nada.

-- 1. Perfis: um por usuário, criado automaticamente no primeiro login
create table if not exists public.perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  nome text,
  plano text not null default 'gratis' check (plano in ('gratis', 'raiox', 'pro', 'admin')),
  cidades text[] not null default '{}',          -- códigos TSE liberados no plano Raio-X
  validade date,                                  -- fim do acesso pago (vazio = sem prazo)
  criado_em timestamptz not null default now()
);
alter table public.perfis enable row level security;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.perfis where id = auth.uid() and plano = 'admin');
$$;

create or replace function public.novo_perfil() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.perfis (id, email, nome)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'))
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists ao_criar_usuario on auth.users;
create trigger ao_criar_usuario after insert on auth.users for each row execute function public.novo_perfil();

drop policy if exists "ver o próprio perfil" on public.perfis;
create policy "ver o próprio perfil" on public.perfis for select using (id = auth.uid() or public.is_admin());
drop policy if exists "admin altera perfis" on public.perfis;
create policy "admin altera perfis" on public.perfis for update using (public.is_admin()) with check (public.is_admin());
-- usuários comuns não alteram o próprio plano: só o admin tem política de update

-- 2. Dados do Raio-X por cidade (carregados pelo coletor com a chave de serviço)
create table if not exists public.raiox (
  cd text primary key,                  -- código TSE da cidade
  uf text not null,
  nome text not null,
  dados jsonb not null,                 -- mesmo formato de data/secao/{cd}.json
  atualizado timestamptz not null default now()
);
alter table public.raiox enable row level security;
drop policy if exists "raiox liberado" on public.raiox;
create policy "raiox liberado" on public.raiox for select using (
  exists (
    select 1 from public.perfis p
    where p.id = auth.uid()
      and (p.validade is null or p.validade >= current_date)
      and (p.plano in ('pro', 'admin') or (p.plano = 'raiox' and raiox.cd = any (p.cidades)))
  )
);
-- lista pública de cidades disponíveis (sem os dados)
create or replace view public.raiox_cidades with (security_invoker = false) as
  select cd, uf, nome, atualizado from public.raiox;
grant select on public.raiox_cidades to anon, authenticated;

-- 3. Interessados (formulário da página de planos)
create table if not exists public.interessados (
  id bigserial primary key,
  nome text not null check (char_length(nome) between 2 and 120),
  email text not null check (email ~* '^[^@\s]+@[^@\s]+\.[^@\s]+$' and char_length(email) <= 200),
  whatsapp text check (whatsapp is null or char_length(whatsapp) <= 30),
  cidade text check (cidade is null or char_length(cidade) <= 120),
  perfil text check (perfil is null or char_length(perfil) <= 60),
  interesse text check (interesse is null or char_length(interesse) <= 120),
  mensagem text check (mensagem is null or char_length(mensagem) <= 1000),
  criado_em timestamptz not null default now()
);
alter table public.interessados enable row level security;
drop policy if exists "qualquer um se cadastra" on public.interessados;
create policy "qualquer um se cadastra" on public.interessados for insert to anon, authenticated with check (true);
drop policy if exists "admin vê interessados" on public.interessados;
create policy "admin vê interessados" on public.interessados for select using (public.is_admin());
grant insert on public.interessados to anon, authenticated;
grant usage, select on sequence public.interessados_id_seq to anon, authenticated;

-- 4. Depois do seu primeiro login no site, rode esta linha trocando o e-mail para virar admin:
-- update public.perfis set plano = 'admin' where email = 'SEU-EMAIL-AQUI';
