import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from "@/integrations/supabase/client";
import { Helmet } from "react-helmet-async";
import { Loader2 } from "lucide-react";

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  created_at: string;
}

export function BlogPage() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPosts = async () => {
      const { data, error } = await supabase
        .from('blog_posts')
        .select('id, title, slug, excerpt, created_at')
        .eq('published', true)
        .order('created_at', { ascending: false });

      if (error) {
        setError('Failed to load posts. Please try again later.');
      } else {
        setPosts(data ?? []);
      }
      setIsLoading(false);
    };

    fetchPosts();
  }, []);

  return (
    <div className="has-navbar">
      <Helmet>
        <title>Blog - Credit Clarity | Credit Repair Tips & Guides</title>
        <meta name="description" content="Expert credit repair tips, dispute guides, and financial advice from the Credit Clarity team." />
        <link rel="canonical" href="https://creditclarity.ai/blog" />
      </Helmet>

      <div className="container py-16 max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-3">
            Credit <span className="text-gold-gradient">Insights</span>
          </h1>
          <p className="text-muted-foreground text-lg">
            Tips, guides, and expert advice to help you take control of your credit.
          </p>
        </div>

        {isLoading && (
          <div className="flex justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-[#D4A853]" />
          </div>
        )}

        {error && (
          <div className="text-center py-16 text-muted-foreground">{error}</div>
        )}

        {!isLoading && !error && posts.length === 0 && (
          <div className="text-center py-16 text-muted-foreground">
            No posts published yet. Check back soon.
          </div>
        )}

        {!isLoading && !error && posts.length > 0 && (
          <div className="grid gap-6">
            {posts.map((post) => (
              <Card key={post.id} className="card-midnight hover:border-[rgba(212,168,83,0.3)] transition-colors">
                <CardHeader>
                  <CardTitle>
                    <Link
                      to={`/blog/${post.slug}`}
                      className="hover:text-[#D4A853] transition-colors"
                    >
                      {post.title}
                    </Link>
                  </CardTitle>
                  <CardDescription>
                    {new Date(post.created_at).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </CardDescription>
                </CardHeader>
                {post.excerpt && (
                  <CardContent>
                    <p className="text-muted-foreground text-sm leading-relaxed">
                      {post.excerpt}
                    </p>
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default BlogPage;
