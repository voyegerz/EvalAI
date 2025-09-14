import { Box, Flex, Icon, Text } from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink } from "@tanstack/react-router";
import { FiBriefcase, FiHome, FiSettings, FiUsers } from "react-icons/fi";
import type { IconType } from "react-icons/lib";
import { Tooltip } from "@/components/ui/tooltip";
import type { UserPublic } from "@/client";

// Updated the items array
const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiBriefcase, title: "Items", path: "/items" }, // Replaced "Items" with "Collections"
  { icon: FiBriefcase, title: "Collections", path: "/collections" }, // Replaced "Items" with "Collections"
  { icon: FiSettings, title: "User Settings", path: "/settings" },
];

interface SidebarItemsProps {
  onClose?: () => void;
  isCollapsed?: boolean;
}

interface Item {
  icon: IconType;
  title: string;
  path: string;
}

const SidebarItems = ({ onClose, isCollapsed }: SidebarItemsProps) => {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"]);

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items;

  const listItems = finalItems.map(({ icon, title, path }) => (
    <Tooltip
      key={title}
      content={title}
      positioning={{ placement: "right-end" }}
      disabled={!isCollapsed}
    >
      <RouterLink
        key={title}
        to={path}
        onClick={onClose}
        activeProps={{
          style: {
            textDecoration: "none",
          },
        }}
      >
        {({ isActive }) => (
          <Flex
            justifyContent={"start"}
            p={4}
            mb={1}
            rounded={"lg"}
            gap={0}
            _hover={{
              background: "gray.subtle",
            }}
            alignItems="center"
            fontSize="sm"
            // Apply active styles here
            bg={isActive ? "gray.subtle" : "transparent"}
            color={isActive ? "blue.500" : "inherit"}
            _dark={{
              bg: isActive ? "gray.subtle" : "transparent",
              color: isActive ? "blue.300" : "inherit",
            }}
          >
            <Icon
              size={"sm"}
              as={icon}
              alignSelf="center"
              mx={isCollapsed ? "auto" : 4}
            />
            <Text ml={2} display={isCollapsed ? "none" : "block"}>
              {title}
            </Text>
          </Flex>
        )}
      </RouterLink>
    </Tooltip>
  ));

  return (
    <>
      <Box>{listItems}</Box>
    </>
  );
};

export default SidebarItems;