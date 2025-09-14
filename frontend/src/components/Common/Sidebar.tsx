import { Box, Flex, IconButton, Text } from "@chakra-ui/react";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CgChevronLeft, CgChevronRight } from "react-icons/cg";
import { FaBars } from "react-icons/fa";
import { FiLogOut } from "react-icons/fi";

import type { UserPublic } from "@/client";
import useAuth from "@/hooks/useAuth";
import {
  DrawerBackdrop,
  DrawerBody,
  DrawerCloseTrigger,
  DrawerContent,
  DrawerRoot,
  DrawerTrigger,
} from "../ui/drawer";
import SidebarItems from "./SidebarItems";

const Sidebar = () => {
  const queryClient = useQueryClient();
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"]);
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false); // New state

  return (
    <>
      {/* Mobile drawer code remains the same */}
      <DrawerRoot
        placement="start"
        open={open}
        onOpenChange={(e) => setOpen(e.open)}
      >
        <DrawerBackdrop />
        <DrawerTrigger asChild>
          <IconButton
            variant="ghost"
            color="inherit"
            display={{ base: "flex", md: "none" }}
            aria-label="Open Menu"
            position="absolute"
            zIndex="100"
            m={4}
          >
            <FaBars />
          </IconButton>
        </DrawerTrigger>
        <DrawerContent maxW="xs">
          <DrawerCloseTrigger />
          <DrawerBody>
            <Flex flexDir="column" justify="space-between">
              <Box>
                <SidebarItems onClose={() => setOpen(false)} />
                <Flex
                  as="button"
                  onClick={() => {
                    logout();
                  }}
                  alignItems="center"
                  gap={4}
                  px={4}
                  py={2}
                >
                  <FiLogOut />
                  <Text>Log Out</Text>
                </Flex>
              </Box>
              {currentUser?.email && (
                <Text fontSize="sm" p={2} truncate maxW="sm">
                  Logged in as: {currentUser.email}
                </Text>
              )}
            </Flex>
          </DrawerBody>
          <DrawerCloseTrigger />
        </DrawerContent>
      </DrawerRoot>

      {/* Desktop */}
      <Box
        display={{ base: "none", md: "flex" }}
        position="sticky"
        bg="bg.subtle"
        rounded={"lg"}
        top={0}
        minW={isCollapsed ? "70px" : "18rem"} // Dynamic width
        w={isCollapsed ? "70px" : "18rem"} // Dynamic width
        h="100vh"
        p={2}
        transition="width 0.5s ease-in-out" // Add a smooth transition
      >
        <Box w="100%">
          {/* Collapse/Expand button */}
          <Flex justify="flex-end" mb={4}>
            <IconButton
              margin={isCollapsed ? "auto" : "0"}
              aria-label="Toggle Sidebar"
              onClick={() => setIsCollapsed(!isCollapsed)}
              variant="ghost"
              _hover={{
                background: "gray.subtle",
              }}
            >
              {isCollapsed ? <CgChevronRight /> : <CgChevronLeft />}
            </IconButton>
          </Flex>

          <SidebarItems isCollapsed={isCollapsed} />
        </Box>
      </Box>
    </>
  );
};

export default Sidebar;
