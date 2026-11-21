// teia · service worker: abre sem internet e recebe lembretes.
const VERSAO = "teia-v1";
const BASE = ["/", "/index.html", "/config.js", "/manifest.webmanifest", "/icones/icone-192.png", "/icones/icone-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(BASE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== VERSAO).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
// Páginas e arquivos do próprio site: rede primeiro, cache se estiver sem internet. Dados (Supabase) nunca vão para o cache.
self.addEventListener("fetch", (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request).then((r) => { if (r.ok) { const c = r.clone(); caches.open(VERSAO).then((cc) => cc.put(e.request, c)); } return r; })
      .catch(() => caches.match(e.request).then((r) => r || caches.match("/index.html")))
  );
});
self.addEventListener("push", (e) => {
  let d = {}; try { d = e.data ? e.data.json() : {}; } catch (_) { d = { corpo: e.data ? e.data.text() : "" }; }
  e.waitUntil(self.registration.showNotification(d.titulo || "Didi", {
    body: d.corpo || "", tag: d.tag || undefined, renotify: !!d.tag, icon: "/icones/icone-192.png", badge: "/icones/icone-192.png",
    data: { url: d.url || "/" }, lang: "pt-BR",
  }));
});
self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((ws) => {
    for (const w of ws) if ("focus" in w) { w.navigate(url).catch(() => {}); return w.focus(); }
    return self.clients.openWindow(url);
  }));
});
