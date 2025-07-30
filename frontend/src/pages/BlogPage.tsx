import { Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const posts = [
  {
    id: 1,
    title: "First Blog Post",
    content: "This is the first blog post.",
  },
  {
    id: 2,
    title: "Second Blog Post",
    content: "This is the second blog post.",
  },
];

export function BlogPage() {
  return (
        <div className="container py-10">
     <Card>
      <CardHeader>
          <CardTitle>Blog</CardTitle>
          <CardDescription>Read our latest blog posts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {posts.map((post) => (
            <div key={post.id}>
              <Link to={`/blog/${post.id}`} className="font-bold text-xl">
                {post.title}
              </Link>
              <p>{post.content}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default BlogPage;