// Barrel export for commonly used UI components
// This allows tree-shaking of unused components and improves import efficiency

// ===== CORE COMPONENTS (High Usage) =====
export { Button, buttonVariants } from './button';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
export { Input } from './input';
export { Label } from './label';
export { Badge, badgeVariants } from './badge';
export { LoadingSpinner, PageLoading, ComponentLoading } from './loading';

// ===== FORM COMPONENTS =====
export { Checkbox } from './checkbox';
export { RadioGroup, RadioGroupItem } from './radio-group';
export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './select';
export { Textarea } from './textarea';
export { Switch } from './switch';

// ===== LAYOUT COMPONENTS =====
export { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogOverlay, DialogTitle, DialogTrigger } from './dialog';
export { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetOverlay, SheetTitle, SheetTrigger } from './sheet';
export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
export { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './accordion';
export { Separator } from './separator';

// ===== FEEDBACK & PROGRESS =====
export { Progress } from './progress';
export { toast, useToast } from './use-toast';
export { Toaster } from './toaster';

// ===== NAVIGATION =====
export { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from './dropdown-menu';

// ===== DATA DISPLAY =====
export { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './table';
export { Avatar, AvatarFallback, AvatarImage } from './avatar';
export { ScrollArea } from './scroll-area';

// ===== SPECIALIZED COMPONENTS (Lazy Load When Needed) =====
// These are not exported by default to enable tree-shaking
// Import directly when needed: import { AlertDialog } from '@/components/ui/alert-dialog'

// Alert & Confirmation
// - AlertDialog, AlertDialogAction, AlertDialogCancel, etc. from './alert-dialog'
// - Alert, AlertDescription, AlertTitle from './alert'

// Advanced Form
// - Form, FormControl, FormDescription, FormField, etc. from './form'
// - Calendar from './calendar'
// - InputOTP, InputOTPGroup, InputOTPSlot from './input-otp'
// - Command, CommandDialog, CommandEmpty, etc. from './command'

// Layout & Navigation
// - Breadcrumb, BreadcrumbItem, BreadcrumbLink, etc. from './breadcrumb'
// - NavigationMenu, NavigationMenuContent, etc. from './navigation-menu'
// - Menubar, MenubarContent, MenubarItem, etc. from './menubar'
// - ContextMenu, ContextMenuContent, etc. from './context-menu'
// - Sidebar, SidebarContent, SidebarFooter, etc. from './sidebar'

// Specialized UI
// - Carousel, CarouselContent, CarouselItem, etc. from './carousel'
// - Chart, ChartContainer, ChartTooltip, etc. from './chart'
// - Drawer, DrawerContent, DrawerDescription, etc. from './drawer'
// - HoverCard, HoverCardContent, HoverCardTrigger from './hover-card'
// - Popover, PopoverContent, PopoverTrigger from './popover'
// - Slider from './slider'
// - Toggle, toggleVariants from './toggle'
// - ToggleGroup, ToggleGroupItem from './toggle-group'
// - Tooltip, TooltipContent, TooltipProvider, TooltipTrigger from './tooltip'
// - Collapsible, CollapsibleContent, CollapsibleTrigger from './collapsible'
// - AspectRatio from './aspect-ratio'
// - Resizable, ResizableHandle, ResizablePanel, ResizablePanelGroup from './resizable'

// Custom Components
// - ProfileStatus from './profile-status'
// - TradelinesStatus from './tradelines-status'

// Types
export type { ToastProps, ToastActionElement } from './toast';