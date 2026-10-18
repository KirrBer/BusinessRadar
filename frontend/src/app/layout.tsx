import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Бизнес-Радар — выбор локации",
  description: "Оценка потенциала бизнес-локации по спросу, окружению и экономике.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
