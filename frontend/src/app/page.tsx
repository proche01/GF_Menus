import { SearchBar } from "@/components/SearchBar";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4">
      <div className="w-full max-w-2xl text-center">
        <h1 className="mb-2 text-5xl font-bold tracking-tight text-emerald-700">
          GF Finder
        </h1>
        <p className="mb-8 text-lg text-gray-600">
          Find gluten-free friendly restaurants with AI-analyzed menus.
          <br />
          Built for celiac and gluten-sensitive diners.
        </p>
        <SearchBar />
      </div>
    </main>
  );
}
