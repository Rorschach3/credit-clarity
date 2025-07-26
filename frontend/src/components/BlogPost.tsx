import { useParams } from "react-router-dom";
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

export function BlogPost() {
  const { id } = useParams();
  const post = posts.find((post) => post.id === Number(id));

  if (!post) {
    return <div>Post not found</div>;
  }

  return (
    <div className="container py-10">
      <Card>
        <CardHeader>
          <CardTitle>{post.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{post.content}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default BlogPost;